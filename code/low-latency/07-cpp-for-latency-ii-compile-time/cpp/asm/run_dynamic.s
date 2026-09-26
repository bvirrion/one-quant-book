	endbr64
	push	r12
	push	rbp
	push	rbx
	mov	rbx, QWORD PTR [rdi]
	mov	r12, QWORD PTR 8[rdi]
	cmp	rbx, r12
	je	.L6
	mov	rbp, rsi
	jmp	.L8
.L14:
	add	rbx, 8
	cmp	r12, rbx
	je	.L6
.L8:
	mov	rdi, QWORD PTR [rbx]
	mov	rsi, rbp
	mov	rax, QWORD PTR [rdi]
	call	[QWORD PTR 16[rax]]
	test	al, al
	jne	.L14
	pop	rbx
	pop	rbp
	pop	r12
	ret
.L6:
	pop	rbx
	mov	eax, 1
	pop	rbp
	pop	r12
	ret
