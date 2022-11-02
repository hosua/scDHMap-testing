import math, os
from time import time

import torch
import torch.nn as nn
from torch.autograd import Variable
from torch.nn import Parameter
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from scDHMap import scDHMap
from embedding_quality_score import get_quality_metrics
import numpy as np
from single_cell_tools import geneSelection
from sklearn.decomposition import PCA
import h5py
import scanpy as sc
from preprocess import read_dataset, normalize, pearson_residuals

torch.set_default_dtype(torch.float64)

data_dir = "my_data/"

try:
    os.makedirs(data_dir)
except FileExistsError:
    pass

if __name__ == "__main__":

    # setting the hyper parameters
    import argparse
    parser = argparse.ArgumentParser(description='train',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--batch_size', default=512, type=int)
    parser.add_argument('--data_file', default='Splatter_simulate_1.h5')
    parser.add_argument('--select_genes', default=1000, type=int)
    parser.add_argument('--n_PCA', default=50, type=int)
    parser.add_argument('--pretrain_iter', default=400, type=int)
    parser.add_argument('--maxiter', default=5000, type=int)
    parser.add_argument('--minimum_iter', default=0, type=int)
    parser.add_argument('--patience', default=150, type=int)
    parser.add_argument('--lr', default=1e-3, type=float)
    parser.add_argument('--likelihood_type', default="zinb", help='must be zinb or nb')
    parser.add_argument('--alpha', default=1000., type=float,
                        help='coefficient of the t-SNE loss')
    parser.add_argument('--beta', default=10., type=float,
                        help='coefficient of the KLD loss')
    parser.add_argument('--prob', default=0., type=float,
                        help='dropout probability')
    parser.add_argument('--perplexity', nargs="+", default=[30.], type=float)
    parser.add_argument('--ae_weights', default=None,
                        help='file name of pretrained model weight; if None, will pretrain from scratch')
    parser.add_argument('--ae_weights_file', default="AE_weights.pth.tar",
                        help='file name to save pretrain model weights')
    parser.add_argument('--save_dir', default= data_dir + 'ES_model/',
                        help='directory to save model weights')
    parser.add_argument('--pretrain_latent_file', default= data_dir + 'ae_latent.txt',
                        help='file name to save latent embedding after pretrain')
    parser.add_argument('--final_latent_file', default= data_dir + 'final_latent.txt',
                        help='file name to save latent embedding after train the whole model')
    parser.add_argument('--final_mean_file', default= data_dir + 'denoised_mean.txt',
                        help='file name to save denoised counts after train the whole model')
    parser.add_argument('--device', default='cuda')

    args = parser.parse_args()

    # X is an array of the shape n_samples by n_features
    data_mat = h5py.File(args.data_file, 'r')
    x = np.array(data_mat['X'])
    data_mat.close()

    importantGenes = geneSelection(x, n=args.select_genes, plot=False)
    x = x[:, importantGenes]

    # Preprocessing scRNA-seq read counts matrix for the autoencoder
    adata0 = sc.AnnData(x)

    adata = read_dataset(adata0,
                     transpose=False,
                     copy=True)

    adata = normalize(adata,
                      size_factors=True,
                      normalize_input=True,
                      logtrans_input=True)

    # Analytic Pearson redisuals normalization and PCA
    X_normalized = pearson_residuals(x, theta=100)
    X_pca = PCA(n_components=args.n_PCA, svd_solver='full').fit_transform(X_normalized)

    print(args)

    print(x.shape)
    print(X_pca.shape)

    # Build the model
    # encoderLayer and decoderLayer set the hidden layer sizes in encoder and decoder
    # z_dim sets the dimension of the latent embedding
    model = scDHMap(input_dim=adata.n_vars, encodeLayer=[128, 64, 32, 16], decodeLayer=[16, 32, 64, 128], 
            batch_size=args.batch_size, activation="elu", z_dim=2, alpha=args.alpha, beta=args.beta, 
            perplexity=args.perplexity, prob=args.prob, likelihood_type=args.likelihood_type, device=args.device).to(args.device)

    print(str(model))

    t0 = time()

    # Pretrain
    if args.ae_weights is None:
        model.pretrain_autoencoder(adata.X.astype(np.float64), adata.raw.X.astype(np.float64), adata.obs.size_factors.astype(np.float64), 
            lr=args.lr, pretrain_iter=args.pretrain_iter, ae_save=True, ae_weights=args.ae_weights_file)
    else:
        if os.path.isfile(args.ae_weights):
            print("==> loading checkpoint '{}'".format(args.ae_weights))
            checkpoint = torch.load(args.ae_weights)
            model.load_state_dict(checkpoint['ae_state_dict'])
        else:
            print("==> no checkpoint found at '{}'".format(args.ae_weights))
            raise ValueError

    print('Pretraining time: %d seconds.' % int(time() - t0))
    ae_latent = model.encodeBatch(torch.tensor(adata.X).double().to(args.device))
    np.savetxt(args.pretrain_latent_file, ae_latent, delimiter=",")

    # Train the model with the hyberbolic t-SNE regularization
    model.train_model(adata.X.astype(np.float64), adata.raw.X.astype(np.float64), adata.obs.size_factors.astype(np.float64), X_pca.astype(np.float64), None,
                    lr=args.lr, maxiter=args.maxiter, minimum_iter=args.minimum_iter,
                    patience=args.patience, save_dir=args.save_dir)
    print('Training time: %d seconds.' % int(time() - t0))

    final_latent = model.encodeBatch(torch.tensor(adata.X).double().to(args.device))
    np.savetxt(args.final_latent_file, final_latent, delimiter=",")

    final_mean = model.decodeBatch(torch.tensor(adata.X).double().to(args.device))
    np.savetxt(args.final_mean_file, final_mean, delimiter=",")
