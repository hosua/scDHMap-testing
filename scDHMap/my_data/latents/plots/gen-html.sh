img_dir="img"
plots=( $( ls ./"$img_dir"/Rplot_*.jpg) )

echo "<!DOCTYPE html>"
echo "<html><body>"
itr=0
for i in "${plots[@]}"
do
	echo "<p>Epoch $itr</p>"
	echo "<img src='$i' width='600' height='600'><br>"
    itr=$((itr+1))
done

echo "</body></html>"
