

current_dir=$(pwd)

cd front 
npm run build
cd "$current_dir"

docker build -t behavior_opt_local -f Dockerfile .

# check exit code
echo $?
