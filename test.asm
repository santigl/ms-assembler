begin:  MOV @125, @124 # Comment
        MOV 0,c
# Not a real code address (!)
        MOV 0, i
while:  CMP i,b
        BEQ end
        ADD a, c
        ADD 1,i
        CMP X,X
        BEQ while
end:    OUT 8, 120
        IN 2, 122