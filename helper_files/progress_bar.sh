#!/bin/bash


calc() {
    echo awk \'BEGIN { print "$@" }\' | /bin/bash 
}

get_integer() {
    echo $(echo "$1" | cut -f1 -d'.')
}

#Draw a Progress Bar on screen
#progressbar <a> <b>
#where a is number of items so far.
#b is total items

progressbar() {



    #Cut out any decimal places to allow interger comparison

    arg1=$(get_integer "$1")
    arg2=$(get_integer "$2")

#We do not want the progress bar extending over 100%, thus
#we prevent the first argument from being larger than the second.

    if [ $arg1 -gt $arg2 ]; then
        arg1=$2
    else
        arg1=$1
    fi

    clc=$(calc "$arg1 / $arg2 * 100")
    clc=$(get_integer $clc)
            
    clc2=$(calc "$clc / 2") 
    clc2=$(get_integer $clc2)
                        
    bar=""
    a=0

    while [ $a -lt $clc2 ]; do
        bar=$bar'='
        a=`expr $a + 1`
    done

    a=0

    while [ $a -lt $(expr 50 - $clc2) ]; do
        bar=$bar'-'
        a=`expr $a + 1`    
    done


echo -n "$clc% [ $bar ] " 

}

progressbar $1 $2
