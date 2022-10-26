root_name="$1"
if [ -z "$root_name" ]; then
	echo "Error: Script requires argument of the root name of the files that should be processed."
fi
latents=( $( ls ./${root_name}_*) )

plot_dir="plots"
mkdir "$plot_dir"

for i in "${latents[@]}"
do
	latent_itr=$(echo $i | grep -o '[0-9]\+')
	Rscript gen_plot.R "$i"
	output_fname="Rplot_$latent_itr.pdf"
	mv Rplots.pdf "$plot_dir/$output_fname"
	echo "Generated latent $latent_itr"
done
