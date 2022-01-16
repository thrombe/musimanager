

SCRIPT=`realpath $0`
SCRIPTPATH=`dirname $SCRIPT`
cd $SCRIPTPATH
# echo $(pwd)

cargo build --release
cp ./target/release/libmusiplayer.so ./musiplayer.so