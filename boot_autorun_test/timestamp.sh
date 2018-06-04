#!/bin/bash
while read x; do
        echo -n $(date +'%y/%m/%d: %H:%M:%S'); 
        echo -n " ";
        echo $x;
done

