poll1:
	IN 2, sw
	CMP sw, 0
	BEQ poll1
	IN 1, a

poll2:
	IN 2, sw
	CMP sw, 0
	BEQ begin

	IN 2, b

while:
	CMP i,b
	BEQ end
	ADD a, c
	ADD 1,i
	CMP X,X
	BEQ while
	OUT 0, c