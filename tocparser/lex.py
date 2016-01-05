"""
Lexer and yaccer for TOC format.
This implementation is limited and tweaked as needed.

PLY is a pure python implementation of lex and yacc, the former for creating tokens from text and the latter for making sense of the order of tokens.
Because of the intended use, the only API provided is a simple read-in-once-and-parse-it.

The BNF is shown below and is implemented PLY-style by including one clause in its own function.

      WHOLE : CD_DA HEADER TRACKS
            | CD_DA        TRACKS

     HEADER : CATALOG TEXT CD_TEXT LCURLY LMAP CDLANGS RCURLY
            |              CD_TEXT LCURLY LMAP CDLANGS RCURLY

       LMAP : LANGUAGE_MAP LCURLY LMAPOPTS RCURLY

   LMAPOPTS : LMAPOPTS LMAPOPT
            : LMAPOPT

    LMAPOPT : NUMBER COLON NUMBER

       TRKS : TRKS TRK
            | TRK

        TRK : COMMENT TRACK AUDIO CPY PE ISRC TEXT TWO_CHANNEL_AUDIO CDT FILELINE
            | COMMENT TRACK AUDIO CPY PE ISRC TEXT TWO_CHANNEL_AUDIO     FILELINE
            | COMMENT TRACK AUDIO CPY PE           TWO_CHANNEL_AUDIO CDT FILELINE
            | COMMENT TRACK AUDIO CPY PE           TWO_CHANNEL_AUDIO     FILELINE

        CPY : NO COPY
            | COPY

         PE : NO PRE_EMPHASIS
            | PRE_EMPHASIS

        CDT : CD_TEXT LCURLY CDLANGS RCURLY

    CDLANGS : CDLANGS CDLANG
            | CDLANG

     CDLANG : LANGUAGE NUMBER LCURLY CDLANGOPTS RCURLY

 CDLANGOPTS : CDLANGOPTS CDLANGOPT
            | CDLANGOPT

  CDLANGOPT : TITLE TEXT
            | PERFORMER TEXT
            | MESSAGE TEXT
            | SIZE_INFO LCURLY NUMBERCSV RCURLY
            | SONGWRITER TEXT
            | COMPOSER TEXT
            | ARRANGER TEXT
            | DISC_ID TEXT
            | TOC_INFO1 LCURLY NUMBERCSV RCURLY
            | UPC_EAT TEXT
            | ISRC TEXT
			| RESERVED4 TEXT

  NUMBERCSV : NUMBERCSV COMMA NUMBER

   FILELINE : FILE TEXT TIMES START TIME
            | FILE TEXT TIMES

      TIMES : NUMBER TIME
            : TIME TIME
"""

import sys

import ply.lex as lex
import ply.yacc as yacc

tokens = (
	'CD_DA',
	'CATALOG',
	'CD_TEXT',
	'TRACK',
	'AUDIO',
	'NO',
	'COPY',
	'PRE_EMPHASIS',
	'ISRC',
	'RESERVED4',
	'TWO_CHANNEL_AUDIO',
	'LCURLY',
	'RCURLY',
	'COLON',
	'START',
	'COMMA',

	'LANGUAGE',
	'LANGUAGE_MAP',
	'FILE',

	'TITLE',
	'PERFORMER',
	'MESSAGE',
	'SIZE_INFO',
	'SONGWRITER',
	'COMPOSER',
	'ARRANGER',
	'DISC_ID',
	'TOC_INFO1',
	'UPC_EAN',


	'TIME',
	'COMMENT',
	'NUMBER',
	'TEXT',
)

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Lexing

# Regular expression rules for tokens
t_CD_DA = r'CD_DA'
t_CATALOG = r'CATALOG'
t_CD_TEXT = r'CD_TEXT'
t_TRACK = r'TRACK'
t_AUDIO = r'AUDIO'
t_NO = r'NO'
t_COPY = r'COPY'
t_PRE_EMPHASIS = r'PRE_EMPHASIS'
t_TWO_CHANNEL_AUDIO = r'TWO_CHANNEL_AUDIO'
t_ISRC = r'ISRC'
t_RESERVED4 = r'RESERVED4'
t_LCURLY = r'\{'
t_RCURLY = r'\}'
t_COLON = r':'
t_START = r'START'
t_COMMA = r','

t_LANGUAGE = r'LANGUAGE'
t_LANGUAGE_MAP = r'LANGUAGE_MAP'
t_FILE = r'FILE'

t_TITLE = r'TITLE'
t_PERFORMER = r'PERFORMER'
t_MESSAGE = r'MESSAGE'
t_SIZE_INFO = r'SIZE_INFO'
t_SONGWRITER = r'SONGWRITER'
t_COMPOSER = r'COMPOSER'
t_ARRANGER = r'ARRANGER'
t_DISC_ID = r'DISC_ID'
t_TOC_INFO1 = r'TOC_INFO1'
t_UPC_EAN = r'UPC_EAN'

def t_TIME(t):
	r'\d+:\d+:\d+'
	return t

def t_COMMENT(t):
	r'\/\/[^\n]*'
	t.value = t.value[2:].lstrip()
	return t

def t_NUMBER(t):
	r'\d+'
	t.value = int(t.value)
	return t

def t_TEXT(t):
	r'"(?:[^"\\]|\\.)*"'
	t.value = t.value[1:-1]
	return t

def t_newline(t):
	r'\n+'
	t.lexer.lineno += len(t.value)

t_ignore = ' \t'

def t_error(t):
	print("Error parsing: %s" %t)
	raise Exception("Error lexing input", str(t))

def lexer(txt):
	l = lex.lex()
	lex.input(txt)

	toks = []
	while True:
		tok = l.token()
		if tok != None:
			toks.append(tok)
		else:
			break

	return toks

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# Parsing

def p_WHOLE_header(p):
	'WHOLE : CD_DA HEADER TRKS'
	p[0] = {'header': p[2], 'tracks': p[3]}

def p_WHOLE(p):
	'WHOLE : CD_DA        TRKS'
	p[0] = {'header': None, 'tracks': p[2]}

def p_HEADER_catalog(p):
	'HEADER : CATALOG TEXT CD_TEXT LCURLY LMAP CDLANGS RCURLY'
	p[0] = {'catalog': p[2], 'map': p[5], 'langs': p[6]}

def p_HEADER(p):
	'HEADER : CD_TEXT LCURLY LMAP CDLANGS RCURLY'
	p[0] = {'catalog': None, 'map': p[3], 'langs': p[4]}

def p_LMAP(p):
	'LMAP : LANGUAGE_MAP LCURLY LMAPOPTS RCURLY'
	p[0] = p[3]

def p_LMAPOPTS(p):
	'LMAPOPTS : LMAPOPTS LMAPOPT'
	p[0] = p[1] + [p[2]]

def p_LMAPOPTS_term(p):
	'LMAPOPTS : LMAPOPT'
	p[0] = [p[1]]

def p_LMAPOPT(p):
	'LMAPOPT : NUMBER COLON NUMBER'
	p[0] = (p[1], p[3])

def p_TRKS(p):
	'TRKS : TRKS TRK'
	p[0] = p[1] + [p[2]]

def p_TRKS_term(p):
	'TRKS : TRK'
	p[0] = [p[1]]

def p_TRK_CDT_ISRC(p):
	'TRK : COMMENT TRACK AUDIO CPY PE TWO_CHANNEL_AUDIO ISRC TEXT CDT FILELINE'
	p[0] = {'comment': p[1], 'copy': p[4], 'preemphasis': p[5], 'channels': 2, 'isrc': p[8], 'text': p[9], 'path': p[10]}

def p_TRK_ISRC(p):
	'TRK : COMMENT TRACK AUDIO CPY PE TWO_CHANNEL_AUDIO ISRC TEXT     FILELINE'
	p[0] = {'comment': p[1], 'copy': p[4], 'preemphasis': p[5], 'channels': 2, 'isrc': p[8], 'text': None, 'path': p[9]}

def p_TRK_CDT(p):
	'TRK : COMMENT TRACK AUDIO CPY PE TWO_CHANNEL_AUDIO           CDT FILELINE'
	p[0] = {'comment': p[1], 'copy': p[4], 'preemphasis': p[5], 'channels': 2, 'isrc': None, 'text': p[7], 'path': p[8]}

def p_TRK(p):
	'TRK : COMMENT TRACK AUDIO CPY PE TWO_CHANNEL_AUDIO               FILELINE'
	p[0] = {'comment': p[1], 'copy': p[4], 'preemphasis': p[5], 'channels': 2, 'isrc': None, 'text': None, 'path': p[7]}

def p_CPY_NO(p):
	'CPY : NO COPY'
	p[0] = False

def p_CPY_YES(p):
	'CPY : COPY'
	p[0] = True

def p_PE_NO(p):
	'PE : NO PRE_EMPHASIS'
	p[0] = False

def p_PE_YES(p):
	'PE : PRE_EMPHASIS'
	p[0] = True

def p_CDT(p):
	'CDT : CD_TEXT LCURLY CDLANGS RCURLY'
	p[0] = p[3]

def p_CDLANGS(p):
	'CDLANGS : CDLANGS CDLANG'
	p[0] = p[1] + [p[2]]

def p_CDLANGS_term(p):
	'CDLANGS : CDLANG'
	p[0] = [p[1]]

def p_CDLANG(p):
	'CDLANG : LANGUAGE NUMBER LCURLY CDLANGOPTS RCURLY'
	p[0] = {'langnum': p[2], 'opts': p[4]}

def p_CDLANGOPTS(p):
	'CDLANGOPTS : CDLANGOPTS CDLANGOPT'
	p[0] = p[1] + [p[2]]

def p_CDLANGOPTS_term(p):
	'CDLANGOPTS : CDLANGOPT'
	p[0] = [p[1]]

def p_CDLANGOPT_title(p):
	'CDLANGOPT : TITLE TEXT'
	p[0] = ('title', p[2])

def p_CDLANGOPT_performer(p):
	'CDLANGOPT : PERFORMER TEXT'
	p[0] = ('performer', p[2])

def p_CDLANGOPT_message(p):
	'CDLANGOPT : MESSAGE TEXT'
	p[0] = ('message', p[2])

def p_CDLANGOPT_sizeinfo(p):
	'CDLANGOPT : SIZE_INFO LCURLY NUMBERCSV RCURLY'
	p[0] = ('sizeinfo', p[3])

def p_CDLANGOPT_songwriter(p):
	'CDLANGOPT : SONGWRITER TEXT'
	p[0] = ('songwriter', p[2])

def p_CDLANGOPT_composer(p):
	'CDLANGOPT : COMPOSER TEXT'
	p[0] = ('composer', p[2])

def p_CDLANGOPT_arranger(p):
	'CDLANGOPT : ARRANGER TEXT'
	p[0] = ('arranger', p[2])

def p_CDLANGOPT_discid(p):
	'CDLANGOPT : DISC_ID TEXT'
	p[0] = ('discid', p[2])

def p_CDLANGOPT_upcean(p):
	'CDLANGOPT : UPC_EAN TEXT'
	p[0] = ('upc_ean', p[2])

def p_CDLANGOPT_isrc(p):
	'CDLANGOPT : ISRC TEXT'
	p[0] = ('isrc', p[2])

def p_CDLANGOPT_reserved4(p):
	'CDLANGOPT : RESERVED4 TEXT'
	p[0] = ('reserved4', p[2])

def p_CDLANGOPT_tocinfo1(p):
	'CDLANGOPT : TOC_INFO1 LCURLY NUMBERCSV RCURLY'
	p[0] = ('tocinfo1', p[3])

def p_NUMBERCSV(p):
	'NUMBERCSV : NUMBERCSV COMMA NUMBER'
	p[0] = p[1] + [p[3]]

def p_NUMBERCSV_term(p):
	'NUMBERCSV : NUMBER'
	p[0] = [p[1]]

def p_FILELINE_start(p):
	'FILELINE : FILE TEXT TIMES START TIME'
	# XXX: ignores the start gap
	p[0] = {'path': p[2], 'times': p[3]}

def p_FILELINE(p):
	'FILELINE : FILE TEXT TIMES'
	p[0] = {'path': p[2], 'times': p[3]}

def p_TIMES_number(p):
	'TIMES : NUMBER TIME'
	p[0] = (p[1], p[2])

def p_TIMES_time(p):
	'TIMES : TIME TIME'
	p[0] = (p[1], p[2])


def p_error(p):
	print("Syntax error")
	print(p)
	raise Exception("Syntax error while yacc'ing the input", str(p))


def yaccer(txt):
	parser = yacc.yacc()
	return parser.parse(txt, lexer=lex.lex())

