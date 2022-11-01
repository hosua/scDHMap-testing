root_dir="$1"
root_name="$2"
final_output_name="$3"
if [ -z "$root_name" ] || [ -z "$root_dir" ] || [ -z "$final_output_name" ]; then
	echo "Usage:"
	echo "arg 1 = root directory to process latents"
	echo "arg 2 = root name of all files to process into gif"
	echo "arg 3 = final output name of .gif file"
fi

txt_dir="${root_dir}/txt"
pdf_dir="${root_dir}/pdf"
mkdir "$pdf_dir"

latents=( $( ls ./${txt_dir}/${root_name}_*) )

# Get all latents into pdf format
for i in "${latents[@]}"
do
	latent_itr=$(echo $i | grep -o '[0-9]\+')
	Rscript gen_plot.R "$i"
	output_fname="Rplot_$latent_itr.pdf"
	mv Rplots.pdf "$pdf_dir/$output_fname"
	echo "Generated latent $latent_itr"
done

# Get all latent pdfs into jpg format
img_dir="${root_dir}/img"
mkdir "$img_dir"

plots=( $( ls ./"$pdf_dir"/Rplot_*.pdf) )

for i in "${plots[@]}"
do
	input_name=$(basename -- $i)
	name="${input_name%.*}"
	output_name="$name.jpg"
	convert "$pdf_dir/$input_name" "$img_dir/$output_name"
	echo "Converted \"$input_name\" -> \"$img_dir/$output_name\""
done

# Convert jpg images into a single gif
convert -delay 3 -loop 0 "$img_dir"/*.jpg "$final_output_name"
echo "Finished generating $final_output_name"


