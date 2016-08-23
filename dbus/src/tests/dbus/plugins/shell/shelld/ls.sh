#!/bin/bash

detail="-1"
dir=$HOME

usage() {
    echo $(basename $0) [--detail] [--directory DIR]
    exit 0
}

set -- `getopt -n$0 -u -a --longoptions="signature detail directory:" "h" "$@"` || usage
[ $# -eq 0 ] && usage

while [ $# -gt 0 ]
do
    case "$1" in
       --signature)
           echo '{"in": [{"detail": "b"},{"directory": "s"}], "out": "s"}'
           exit 0
           ;;
       --detail)
           detail="-la"
           ;;
       --directory)
           dir=$2
           shift
           ;;
       -h)        usage;;
       --)        shift;break;;
       -*)        usage;;
       *)         break;;
    esac
    shift
done
ls $detail $dir