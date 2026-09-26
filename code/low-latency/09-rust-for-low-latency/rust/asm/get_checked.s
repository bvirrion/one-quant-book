	push	rax
	cmp	rdx, rsi
	jae	.LBB15_1
	mov	eax, dword ptr [rdi + 4*rdx]
	pop	rcx
	ret
.LBB15_1:
	lea	rax, [rip + .Lanon.3be006c39583d7e749c2975be3997e3f.5]
	mov	rdi, rdx
	mov	rdx, rax
	call	qword ptr [rip + _RNvNtCs4NRVxsYgnAr_4core9panicking18panic_bounds_check@GOTPCREL]
	ud2
.LBB15_4:
	call	qword ptr [rip + _RNvNtCs4NRVxsYgnAr_4core9panicking19panic_cannot_unwind@GOTPCREL]
