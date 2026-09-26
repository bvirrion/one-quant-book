	test	rsi, rsi
	je	.LBB16_1
	cmp	rsi, 4
	jae	.LBB16_5
	xor	eax, eax
	xor	ecx, ecx
	jmp	.LBB16_4
.LBB16_1:
	xor	eax, eax
	ret
.LBB16_5:
	mov	rcx, rsi
	and	rcx, -4
	pxor	xmm1, xmm1
	xor	eax, eax
	pxor	xmm2, xmm2
	pxor	xmm0, xmm0
.LBB16_6:
	movq	xmm3, qword ptr [rdi + 4*rax]
	movq	xmm4, qword ptr [rdi + 4*rax + 8]
	punpckldq	xmm3, xmm1
	paddq	xmm2, xmm3
	punpckldq	xmm4, xmm1
	paddq	xmm0, xmm4
	add	rax, 4
	cmp	rcx, rax
	jne	.LBB16_6
	paddq	xmm0, xmm2
	pshufd	xmm1, xmm0, 238
	paddq	xmm1, xmm0
	movq	rax, xmm1
	jmp	.LBB16_8
.LBB16_4:
	mov	edx, dword ptr [rdi + 4*rcx]
	inc	rcx
	add	rax, rdx
.LBB16_8:
	cmp	rsi, rcx
	jne	.LBB16_4
	ret
