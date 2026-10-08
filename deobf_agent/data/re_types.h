/*
 * re_types.h — IDA Pro / IDA Free (Hex-Rays), Ghidra va angr psevdokodida
 * uchraydigan maxsus turlar va makroslarni gcc/clang tushunadigan qilib e'lon qiladi.
 *
 * Nima uchun kerak: dekompilyator chiqargan psevdokod "deyarli C" bo'ladi, lekin
 * `_DWORD`, `undefined4`, `__fastcall`, `LODWORD(x)` kabi nostandart nomlar ishlatadi.
 * Bu fayl ularni standart C turlariga bog'laydi, shunda psevdokodning o'zini ham,
 * LLM yaratgan kodni ham kompilyatsiya qilib tekshira olamiz.
 */
#ifndef DEOBF_RE_TYPES_H
#define DEOBF_RE_TYPES_H

#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

/* ---------- IDA / Hex-Rays ---------- */
#ifndef __int8
#define __int8 char
#endif
#ifndef __int16
#define __int16 short
#endif
#ifndef __int32
#define __int32 int
#endif
#ifndef __int64
#define __int64 long long
#endif

typedef uint8_t  _BYTE;
typedef uint16_t _WORD;
typedef uint32_t _DWORD;
typedef uint64_t _QWORD;
typedef int8_t   _BOOL1;
typedef int16_t  _BOOL2;
typedef int32_t  _BOOL4;
typedef int64_t  _BOOL8;
typedef uint8_t  _UNKNOWN;

#define __fastcall
#define __cdecl
#define __stdcall
#define __thiscall
#define __usercall
#define __userpurge
#define __noreturn
#define __spoils(...)
#define __hidden
#define __return_ptr
#define __struct_ptr
#define __far
#define __near
#define __ptr32
#define __ptr64

#define LOBYTE(x)   (*((_BYTE *)&(x)))
#define LOWORD(x)   (*((_WORD *)&(x)))
#define LODWORD(x)  (*((_DWORD *)&(x)))
#define HIBYTE(x)   (*((_BYTE *)&(x) + sizeof(x) - 1))
#define HIWORD(x)   (*((_WORD *)&(x) + sizeof(x) / 2 - 1))
#define HIDWORD(x)  (*((_DWORD *)&(x) + 1))
#define BYTEn(x, n) (*((_BYTE *)&(x) + (n)))
#define BYTE1(x)    BYTEn(x, 1)
#define BYTE2(x)    BYTEn(x, 2)
#define BYTE3(x)    BYTEn(x, 3)
#define SLOBYTE(x)  (*((int8_t *)&(x)))
#define SLODWORD(x) (*((int32_t *)&(x)))
#define SHIDWORD(x) (*((int32_t *)&(x) + 1))
#define __PAIR64__(high, low) (((uint64_t)(high) << 32) | (uint32_t)(low))

static inline uint8_t  __ROL1__(uint8_t v, int n)  { n &= 7;  return (uint8_t)((v << n) | (v >> ((8 - n) & 7))); }
static inline uint8_t  __ROR1__(uint8_t v, int n)  { n &= 7;  return (uint8_t)((v >> n) | (v << ((8 - n) & 7))); }
static inline uint16_t __ROL2__(uint16_t v, int n) { n &= 15; return (uint16_t)((v << n) | (v >> ((16 - n) & 15))); }
static inline uint16_t __ROR2__(uint16_t v, int n) { n &= 15; return (uint16_t)((v >> n) | (v << ((16 - n) & 15))); }
static inline uint32_t __ROL4__(uint32_t v, int n) { n &= 31; return (v << n) | (v >> ((32 - n) & 31)); }
static inline uint32_t __ROR4__(uint32_t v, int n) { n &= 31; return (v >> n) | (v << ((32 - n) & 31)); }
static inline uint64_t __ROL8__(uint64_t v, int n) { n &= 63; return (v << n) | (v >> ((64 - n) & 63)); }
static inline uint64_t __ROR8__(uint64_t v, int n) { n &= 63; return (v >> n) | (v << ((64 - n) & 63)); }

/* ---------- Ghidra ---------- */
typedef uint8_t  undefined;
typedef uint8_t  undefined1;
typedef uint16_t undefined2;
typedef uint32_t undefined3;
typedef uint32_t undefined4;
typedef uint64_t undefined5;
typedef uint64_t undefined6;
typedef uint64_t undefined7;
typedef uint64_t undefined8;
typedef uint8_t  byte;
typedef uint16_t word;
typedef uint32_t dword;
typedef uint64_t qword;
typedef unsigned char      uchar;
typedef unsigned short     ushort;
typedef unsigned int       uint;
typedef unsigned long      ulong;
typedef long long          longlong;
typedef unsigned long long ulonglong;
typedef void              *pointer;
typedef void               code;
#ifndef __cplusplus
#ifndef bool
typedef _Bool bool;
#define true 1
#define false 0
#endif
#endif

#define CONCAT11(a, b) ((uint16_t)(((uint16_t)(uint8_t)(a) << 8) | (uint8_t)(b)))
#define CONCAT22(a, b) ((uint32_t)(((uint32_t)(uint16_t)(a) << 16) | (uint16_t)(b)))
#define CONCAT44(a, b) ((uint64_t)(((uint64_t)(uint32_t)(a) << 32) | (uint32_t)(b)))
#define SUB41(x, n) ((uint8_t)((uint32_t)(x) >> ((n) * 8)))
#define SUB42(x, n) ((uint16_t)((uint32_t)(x) >> ((n) * 8)))
#define SUB81(x, n) ((uint8_t)((uint64_t)(x) >> ((n) * 8)))
#define SUB84(x, n) ((uint32_t)((uint64_t)(x) >> ((n) * 8)))
#define ZEXT14(x) ((uint32_t)(uint8_t)(x))
#define ZEXT24(x) ((uint32_t)(uint16_t)(x))
#define ZEXT48(x) ((uint64_t)(uint32_t)(x))
#define SEXT14(x) ((int32_t)(int8_t)(x))
#define SEXT24(x) ((int32_t)(int16_t)(x))
#define SEXT48(x) ((int64_t)(int32_t)(x))

#endif /* DEOBF_RE_TYPES_H */
