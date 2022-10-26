library(ggplot2)
library(RColorBrewer)

colorvector <- c("#e6194b", "#3cb44b", "#ffe119", "#0082c8",

				 "#f58231", "#911eb4", "#46f0f0", "#f032e6",

				 "#d2f53c", "#fabebe", "#008080", "#e6beff",

				 "#aa6e28", "#fffac8", "#800000", "#aaffc3",

				 "#6666ff", "#cc33ff")


args = commandArgs(trailingOnly=TRUE)
latent_file = args[1]

paul.latent <- read.table(latent_file, sep=",")

paul.cell_type <- readLines("Paul_celltypes.txt")

mycolors0 <- colorRampPalette(brewer.pal(9, "Set1"))(20)

paul.dat <- data.frame(paul.latent, `Cell type`=paul.cell_type, check.names = F)

ggplot(paul.dat, aes(x=V1, y=V2, color=`Cell type`)) + geom_point(size=.5) +

annotate("path", x=0+1*cos(seq(0,2*pi,length.out=100)), y=0+1*sin(seq(0,2*pi,length.out=100))) +

scale_color_manual(values=mycolors0) +

guides(colour = guide_legend(override.aes = list(size=3), ncol=2)) + coord_fixed(ratio=1) +

theme_classic() + theme(axis.title=element_blank(), axis.ticks=element_blank(), axis.text=element_blank(), axis.line=element_blank(), legend.title=element_blank())
