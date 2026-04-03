# Error analysis of the syntactic validation errors

## too-many-subjects error

### In the sentence below, two contiguos nouns with xpos N$ are incorrectly treated as two subjects, while the second one is a possessive modifier of the first (see gold annoation). 


#### converter output
```conllu
# sent_id = ped-gramm-18
# sent_uid = 582429f2-67d5-4077-b209-6deb7b5df54f
# text = ica lidGegi loligi idei liGeladi.
# text_orig = ica lidGegi loligi idei liGeladi
# text_por_orig = a deliciosa comida está na casa dela/dele
# text_por = a deliciosa comida está na casa dela/dele.
1	ica	ica	DET	D	Gender=Masc|Number=Sing|PronType=Dem	2	det	_	TokenRange=0:3
2	lidGegi	idi	NOUN	N$	Person[psor]=3	4	nsubj	_	TokenRange=4:11
3	loligi	oligi	NOUN	N$	Person[psor]=3	4	nsubj	_	TokenRange=12:18
4	idei	dei	VERB	VB	_	0	root	_	TokenRange=19:23
5	liGeladi	geladi	NOUN	N$	Gender=Masc|Number=Sing|Person[psor]=3	4	obj	_	SpaceAfter=No|TokenRange=24:32
6	.	.	PUNCT	PUNCT	_	4	punct	_	SpaceAfter=No|TokenRange=32:33
```

#### gold annotation

```conllu
# sent_id = ped-gramm-18
# sent_uid = 582429f2-67d5-4077-b209-6deb7b5df54f
# text = ica lidGegi loligi idei liGeladi.
# text_orig = ica lidGegi loligi idei liGeladi
# text_por_orig = a deliciosa comida está na casa dela/dele
# text_por_alt1 = A deliciosa comida está na casa dela.
# text_por_alt2 = A deliciosa comida está na casa dele.
# text_por_lit = A gostosura da comida dele/dela está na casa dela/dele.
1	ica	ica	DET	D	Gender=Masc|Number=Sing|PronType=Dem	2	det	_	TokenRange=0:3
2	lidGegi	idi	NOUN	N$	Gender=Masc|Number=Sing|Person[psor]=3	4	nsubj	_	TokenRange=4:11
3	loligi	oligi	NOUN	N$	Gender=Masc|Number=Sing|Person[psor]=3	2	nmod:poss	_	TokenRange=12:18
4	idei	dei	VERB	VB	Mood=Ind|Person[erg]=3|VerbForm=Fin	0	root	_	TokenRange=19:23
5	liGeladi	iGeladi	NOUN	N$	Gender=Masc|Number=Sing|Person[psor]=3	4	obj	_	SpaceAfter=No|TokenRange=24:32
6	.	.	PUNCT	PUNCT	_	4	punct	_	SpaceAfter=No|TokenRange=32:33
```

### second example with the too-many-subjects error

#### converter output

```conllu
# sent_id = ped-gramm-30
# sent_uid = 7b806584-75e5-4017-b9e2-ba97458903bd
# text = Eyodi ane niganaGacanajo.
# text_orig = Eyodi ane niganaGacanajo
# text_por_orig = Meu pai que era cantor (explicativa)
# text_por = Meu pai que era cantor (explicativa).
1	Eyodi	eyodi	NOUN	N$	_	3	nsubj	_	TokenRange=0:5
2	ane	ane	PRON	WPRO	PronType=Rel	3	nsubj	_	TokenRange=6:9
3	niganaGacanajo	niganagacanajo	NOUN	N	_	0	root	_	SpaceAfter=No|TokenRange=10:24
4	.	.	PUNCT	PUNCT	_	3	punct	_	SpaceAfter=No|TokenRange=24:25
```

#### updated version of the original annotation (txt view), showing the nested NP structure

```
================================================================================
Sentence 30
================================================================================
path: $.pages[0].sentences[29]
uid: 7b806584-75e5-4017-b9e2-ba97458903bd
text: Eyodi ane niganaGacanajo
visible: None
container_meta:
  content: ajo liwatece ja iwaGadi
  contents: {"pt-br": "A canoa dele/a é/está pesada"}
  uid: 28eeb8a0-d923-4d75-aebe-599aadddfbbb
translations:
  pt-br: Meu pai que era cantor (explicativa)

proto-conllu:
  <none>

chunks:
  span=1-4 type=IP-MAT level=0
  span=1-4 type=NP level=1
  span=2-4 type=CP-REL level=2
  span=2-2 type=WNP level=3
  span=3-4 type=IP-SUB level=3
  span=4-4 type=NP level=4
  span=3-3 type=NP-TRACE level=4

tokens:
  p=1   v='Eyodi'            t='N$'         l=1   gloss-br='meu pai'
  p=2   v='ane'              t='WPRO'       l=3   gloss-br='que'
  p=3   v='*T*'              t=None         l=4   gloss-br=None
  p=4   v='niganaGacanajo'   t='N'          l=4   gloss-br=None

conllu/token count check:
  tokens=4  proto-conllu=0e3-648f-4081-a4ad-110337326750"
}
```

#### gold annotation

```conllu
# sent_id = ped-gramm-30
# sent_uid = 7b806584-75e5-4017-b9e2-ba97458903bd
# text = Eyodi ane niganaGacanajo.
# text_orig = Eyodi ane niganaGacanajo
# text_por_orig = Meu pai que era cantor (explicativa)
# text_por = Meu pai, que era cantor.
1	Eyodi	eyodi	NOUN	N$	Gender=Masc|Number=Sing|Number[psor]=Sing|Person[psor]=1	0	root	_	TokenRange=0:5
2	ane	ane	PRON	WPRO	PronType=Rel	3	nsubj	_	TokenRange=6:9
3	niganaGacanajo	niganagacanajo	NOUN	N	Gender=Masc|Number=Sing	1	acl:relcl	_	SpaceAfter=No|TokenRange=10:24
4	.	.	PUNCT	PUNCT	_	1	punct	_	SpaceAfter=No|TokenRange=24:25

```

## too-many-objects error

### converter output

```conllu
# sent_id = ped-gramm-28
# sent_uid = ee1a1190-7803-404c-83f6-49d3ccf63b0d
# text = Eyodi dowediteloco naodigijedi micoataGa daGa me lionigipi.
# text_orig = Eyodi dowediteloco naodigijedi micoataGa daGa me lionigipi
# text_por_orig = meu pai cuida da plantação de flores como filhas
# text_por = meu pai cuida da plantação de flores como filhas.
1	Eyodi	eyodi	NOUN	N$	_	2	nsubj	_	TokenRange=0:5
2	dowediteloco	dowediteloco	VERB	VBAPL	Voice=Appl	0	root	_	TokenRange=6:18
3	naodigijedi	naodigijedi	NOUN	N	_	2	obj	_	TokenRange=19:30
4	micoataGa	taGa	X	CD	_	2	dep	_	TokenRange=31:40
5	daGa	daga	SCONJ	C	_	2	dep	_	TokenRange=41:45
6	me	me	SCONJ	C	_	2	dep	_	TokenRange=46:48
7	lionigipi	lionigipi	NOUN	N$	_	2	obj	_	SpaceAfter=No|TokenRange=49:58
8	.	.	PUNCT	PUNCT	_	2	punct	_	SpaceAfter=No|TokenRange=58:59
```

### updated analysis in the original treebank (txt view)

The word "lionigipi" is inside another IP projection, namely IP-SUB:

```
================================================================================
Sentence 28
================================================================================
path: $.pages[0].sentences[27]
uid: ee1a1190-7803-404c-83f6-49d3ccf63b0d
text: Eyodi dowediteloco naodigijedi micoataGa daGa me lionigipi
visible: None
container_meta:
  content: ajo liwatece ja iwaGadi
  contents: {"pt-br": "A canoa dele/a é/está pesada"}
  uid: 28eeb8a0-d923-4d75-aebe-599aadddfbbb
translations:
  pt-br: meu pai cuida da plantação de flores como filhas

proto-conllu:
  <none>

chunks:
  span=1-7 type=IP-MAT level=0
  span=1-1 type=NP level=1
  span=3-3 type=NP-APL level=1
  span=6-7 type=CP-me level=1
  span=7-7 type=IP-SUB level=2
  span=7-7 type=NP level=3

tokens:
  p=1   v='Eyodi'            t='N$'         l=1   gloss-br='meu pai'
  p=2   v='dowediteloco'     t='VBAPL'      l=0   gloss-br='cuida de'
  p=3   v='naodigijedi'      t='N'          l=1   gloss-br='plantação de flores'
  p=4   v='micoataGa'        t='CD'         l=0   gloss-br='como'
      splits:
        [1] v='me'         t='c'        gloss-br=None fn=False idx=None
        [2] v='i'          t='Gnr'      gloss-br=None fn=None idx=None
        [3] v='ca'         t='Ncl'      gloss-br=None fn=None idx=None
        [4] v='wa'         t='Plu'      gloss-br=None fn=None idx=None
        [5] v='taGa'       t='Apl'      gloss-br='com' fn=None idx=None
  p=5   v='daGa'             t='C'          l=0   gloss-br='se'
  p=6   v='me'               t='C'          l=1   gloss-br='que'
  p=7   v='lionigipi'        t='N$'         l=3   gloss-br='filhas'

conllu/token count check:
  tokens=7  proto-conllu=0
```