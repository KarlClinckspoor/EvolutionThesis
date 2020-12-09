echo "" > log.txt
echo "" > err.txt

cd Tese
git checkout master --force
hash="$(git log --oneline | awk '{print $1}')"
IFS='\n' read -r -a array <<< "$hash"
echo "$array"
#echo "$hash"
for h in "${array[@]}"; do
	echo "$h"
	#bash ../compilar_copiar.sh "$h"
done
