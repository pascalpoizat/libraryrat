#!/bin/bash
egrep -o '"ee":([^,]*),' $1 | cut -d ':' -f 2- | cut -d '"' -f 2
