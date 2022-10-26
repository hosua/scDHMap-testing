plots=( $( ls ./Rplot_*.pdf) )

for i in "${plots[@]}"
do
	input_name=$(basename -- $i)
	name="${input_name%.*}"
	output_name="$name.jpg"
	convert "$input_name" "$output_name"
	echo "Converted \"$input_name\" -> \"$output_name\""
done
