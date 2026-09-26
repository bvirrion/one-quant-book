	endbr64
	mov	rdx, QWORD PTR [rsi]
	mov	eax, DWORD PTR 8[rsi]
	xor	r8d, r8d
	add	rax, QWORD PTR 16[rsi]
	xor	rax, rdx
	mov	QWORD PTR 16[rsi], rax
	cmp	rdx, QWORD PTR 8[rdi]
	jge	.L1
	add	QWORD PTR [rdi], rax
	mov	r8d, 1
.L1:
	mov	eax, r8d
	ret
