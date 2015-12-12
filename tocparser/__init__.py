"""
TOC file parser as produced by cdrdao.
The TOC can contain metadata in addition to the track listing and times.
"""

__all__ = ['TOC', 'MSF', 'LangCodeToName', 'LangCodeTo2Letter', 'version']

from .lex import lexer, yaccer

class MSF:
	"""
	Container for minute, second, frame format that times in CDs use.
	There are 75 frames per second.
	"""

	def __init__(self, m,s,f):
		"""
		Supply minutes, seconds, and frames.
		Each will be converted to an integer and normalized appropriately.
		"""

		# Ensure they are integers
		m = int(m)
		s = int(s)
		f = int(f)

		# Reduce to m=[0,infinity), s=[0,59], f=[0,74]
		s += int(f / 75)
		f = f % 75

		m += int(s / 60)
		s = s % 60

		# Assign
		self.m = m
		self.s = s
		self.f = f

	def __str__(self):
		"""
		Gets MSF in "MM:SS.FF" format and zero-padded.
		"""
		return "%02d:%02d.%02d" % (self.m, self.s, self.f)

	def __repr__(self):
		return "<MSF m=%d s=%d f=%d str=%s>" % (self.m, self.s, self.f, str(self))

	def __add__(self, b):
		"""
		Adds two MSF objects together component-by-component and normalizes the result.
		"""
		return MSF(self.M + b.M, self.S + b.S, self.F + b.F)

	@staticmethod
	def Create(val):
		"""
		Creates an MSF object.
		If @val is an integer then it is assumed to be the number of frames.
		If
		"""
		if type(val) == int:
			return MSF(0,0,val)
		elif type(val) == str:
			parts = val.split(':')
			if len(parts) != 3:
				raise ValueError("Expected M:S:F formation, didn't get it '%s'" % (val,))
			return MSF(*parts)
		else:
			raise TypeError("Unable to handle '%s' and convert to MSF format." % str(type(val)))

	@property
	def M(self):
		"""
		Minutes.
		"""
		return self.m

	@property
	def S(self):
		"""
		Seconds. Bounded to [0, 59].
		"""
		return self.s

	@property
	def F(self):
		"""
		Frames. Bounded to [0, 74] and is 1/75th per second per frame.
		"""
		return self.f

	@property
	def TotalFrames(self):
		"""
		Total frames for this time.
		Can be fed into the @f parameter to the constructor to normalize to MSF format.
		"""
		return self.F + (self.S * 75) + (self.M * 60 * 75)


	@staticmethod
	def Zero():
		"""
		Gets an MSF of zero.
		"""
		return MSF(0,0,0)

class TOC:
	"""
	Table of contents of a CD.
	"""

	def __init__(self):
		pass

	@staticmethod
	def load(path):
		"""
		Load from file.
		"""
		with open(path, 'rb') as f:
			dat = f.read()
			return TOC.loads(dat)
	
	@staticmethod
	def loads(txt):
		"""
		Load from string.
		"""
		t = TOC()
		t.parse(txt.decode('latin-1'))

		return t


	def parse(self, txt):
		"""
		Parse the text @txt and populate this object with the parsed information.
		"""

		# Lex & Yacc out the structure
		p = yaccer(txt)

		# Get the header information
		h = Header(p['header'])
		ts = []

		# Iterate through the tracks
		for track in p['tracks']:
			t = Track(track)
			ts.append(t)

		# Assign to this object
		self._header = h
		self._tracks = ts

	@property
	def Header(self):
		"""
		Gets the hader of the TOC file.
		"""
		return self._header

	@property
	def Tracks(self):
		"""
		Gets all tracks.
		"""
		return self._tracks

	def GetTrack(self, num):
		"""
		Gets the track given @num, a one-based track number.
		"""
		for track in self._tracks:
			if track.Number == num:
				return trac

		return None

	@property
	def TotalLength(self):
		"""
		Gets the total length of the CD by adding the durations of all the tracks.
		"""
		z = MSF.Zero()

		for t in self.Tracks:
			z = z + t.FileDuration

		return z

class Header:
	"""
	Represents the header of a TOC file.
	Most importantly, it contains meta information.
	"""

	_langmap = None
	_meta = None

	def __init__(self, p):
		self._langmap = {}
		self._meta = {}

		self._catalog = p['catalog']

		for entry in p['map']:
			self._langmap[ entry[0] ] = (entry[1], LangCodeTo2Letter(entry[1]), LangCodeToName(entry[1]))

		for entry in p['langs']:
			os = {}
			for o in entry['opts']:
				os[ o[0] ] = o[1]

			self._meta[ entry['langnum'] ] = os

	@property
	def LangMap(self):
		"""
		Gets the langauge map.
		The keys are the language index used in the track information.
		The values are a three-tuple of (language code, ISO 3166-1 alpha-2 country code, country name) for where it makes sense.
		For example, 9 is english and yields (9, 'EN', 'English')
		Probably not the best mapping but deal with it...or fix it.
		"""
		return self._langmap

	@property
	def Catalog(self):
		"""
		Thirteen character catalog number as registered with the RIAA.
		"""
		return self._catalog

	@property
	def Meta(self):
		"""
		Gets the meta information that is keyed on the language map index and to a dictionary of string keys and values.
		"""
		return self._meta

class Track:
	"""
	Represents a track.
	"""

	_num = None
	_copy = None
	_preemphasis = None
	_channels = None
	_isrc = None
	_meta = None
	_filepath = None
	_filestart = None
	_fileend = None
	_fileduration = None

	def __init__(self, p):
		parts = p['comment'].split(' ')
		if len(parts) == 2 and parts[0].lower() == 'track':
			self._num = int(parts[1])

		self._copy = p['copy']
		self._preemphasis = p['preemphasis']
		self._channels = p['channels']
		self._meta = {}

		for entry in p['text']:
			os = {}
			for o in entry['opts']:
				os[ o[0] ] = o[1]

			self._meta[ entry['langnum'] ] = os

		self._isrc = p['isrc']
		self._filepath = p['path']['path']

		# Start and duration are given, add them to get the end
		self._filestart = MSF.Create( p['path']['times'][0] )
		self._fileduration = MSF.Create( p['path']['times'][1] )
		self._fileend = self._filestart + self._fileduration

	@property
	def Number(self):
		"""
		Track number.
		"""
		return self._num

	@property
	def Copy(self):
		"""
		True or False for permitting copying.
		"""
		return self._copy

	@property
	def PreEmphasis(self):
		"""
		True or False for pre-emphasis.
		"""
		return self._preemphasis

	@property
	def Channels(self):
		"""
		Number of channels (always 2 for CDs).
		"""
		return self._channels

	@property
	def ISRC(self):
		"""
		ISRC (Internationl Standard Recording Code) that is unique to each track.
		"""
		return self._isrc

	@property
	def Meta(self):
		"""
		Meta information about this track (Title, Performer, etc.)
		"""
		return self._meta

	@property
	def FilePath(self):
		"""
		Path to the file where this track is located
		"""
		return self._filepath

	@property
	def FileStart(self):
		"""
		Start time of this track in MSF format.
		"""
		return self._filestart

	@property
	def FileEnd(self):
		"""
		End time of this track in MSF format.
		"""
		return self._fileend

	@property
	def FileDuration(self):
		"""
		Duration of this track in MSF format.
		"""
		return self._fileduration


def LangCodeToName(idx):
	"""
	Converts language code found in the TOC to the ISO 3166-1 alpha-2 value that roughly matches the location
	of the language. Not all entries have them (empty string if so) and probably shouldn't be used.
	"""
	if idx in _langcodes:
		return _langcodes[idx][1]
	else:
		return None

def LangCodeTo2Letter(idx):
	"""
	Converts language code found in the TOC to the name of the language per that found in libcdio's documentation (see comment below in source code).
	"""
	if idx in _langcodes:
		return _langcodes[idx][0]
	else:
		return None

# Table 1.3 from https://www.gnu.org/software/libcdio/cd-text-format.html
# https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
# combined with the ISO 3166-1 alpha-2 codes
_langcodes = {}
_langcodes[0]  = ('??', 'Unknown')
_langcodes[1]  = ('AL', 'Albania')
_langcodes[2]  = ('', 'Breton')
_langcodes[3]  = ('', 'Catalan')
_langcodes[4]  = ('HR', 'Croatian')
_langcodes[5]  = ('', 'Welsh')
_langcodes[6]  = ('CZ', 'Czech')
_langcodes[7]  = ('DK', 'Danish')
_langcodes[8]  = ('DE', 'German')
_langcodes[9]  = ('EN', 'English')
_langcodes[10] = ('ES', 'Spanish')
_langcodes[11] = ('', 'Esperanto')
_langcodes[12] = ('EE', 'Estonian')
_langcodes[13] = ('', 'Basque')
_langcodes[14] = ('FO', 'Faroese')
_langcodes[15] = ('FR', 'French')
_langcodes[16] = ('', 'Frisian')
_langcodes[17] = ('', 'Irish')
_langcodes[18] = ('', 'Faelic')
_langcodes[19] = ('', 'Galician')
_langcodes[20] = ('IS', 'Iceland')
_langcodes[21] = ('IT', 'Italian')
_langcodes[22] = ('', 'Lappish')
_langcodes[23] = ('', 'Latin')
_langcodes[24] = ('LV', 'Latvian')
_langcodes[25] = ('LU', 'Luxembourgian')
_langcodes[26] = ('LT', 'Lithuanian')
_langcodes[27] = ('HU', 'Hungarian')
_langcodes[28] = ('MT', 'Maltese')
_langcodes[29] = ('NL', 'Dutch')
_langcodes[30] = ('NO', 'Norwegian')
_langcodes[31] = ('', 'Occitan')
_langcodes[32] = ('PL', 'Polish')
_langcodes[33] = ('PT', 'Portuguese')
_langcodes[34] = ('RO', 'Romania')
_langcodes[35] = ('', 'Romanish')
_langcodes[36] = ('RS', 'Serbian')
_langcodes[37] = ('SK', 'Slovak')
_langcodes[38] = ('SI', 'Slovenian')
_langcodes[39] = ('FI', 'Finnish')
_langcodes[40] = ('SE', 'Swedish')
_langcodes[41] = ('TR', 'Turkish')
_langcodes[42] = ('', 'Flemish')
_langcodes[43] = ('', 'Wallon')

# Jumps to 0x45 = 69
_langcodes[69] = ('', 'Zulu')
_langcodes[70] = ('VN', 'Vietnamese')
_langcodes[71] = ('UZ', 'Uzbek')
_langcodes[72] = ('', 'Urdu')
_langcodes[73] = ('UA', 'Ukranian')
_langcodes[74] = ('TH', 'Thai')
_langcodes[75] = ('', 'Telugu')
_langcodes[76] = ('', 'Tatar')
_langcodes[77] = ('', 'Tamil')
_langcodes[78] = ('', 'Tadzhik')
_langcodes[79] = ('', 'Swahili')
_langcodes[80] = ('', 'Sranan Tongo')
_langcodes[81] = ('SO', 'Somali')
_langcodes[82] = ('', 'Sinhalese')
_langcodes[83] = ('', 'Shona')
_langcodes[84] = ('', 'Serbo-croat')
_langcodes[85] = ('', 'Ruthenian')
_langcodes[86] = ('RU', 'Russian')
_langcodes[87] = ('', 'Quechua')
_langcodes[88] = ('', 'Pushtu')
_langcodes[89] = ('', 'Punjabi')
_langcodes[90] = ('', 'Persian')
_langcodes[91] = ('', 'Papamiento')
_langcodes[92] = ('', 'Oriya')
_langcodes[93] = ('NP', 'Nepali')
_langcodes[94] = ('', 'Ndebele')
_langcodes[95] = ('', 'Marathi')
_langcodes[96] = ('MD', 'Moldavian')
_langcodes[97] = ('MY', 'Malaysian')
_langcodes[98] = ('', 'Malagasay')
_langcodes[99] = ('MK', 'Macedonian')
_langcodes[100] = ('LA', 'Laotian')
_langcodes[101] = ('KR', 'Korean')
_langcodes[102] = ('', 'Khmer')
_langcodes[103] = ('', 'Kazakh')
_langcodes[104] = ('', 'Kannada')
_langcodes[105] = ('JP', 'Japanese')
_langcodes[106] = ('ID', 'Indonesian')
_langcodes[107] = ('', 'Hindi')
_langcodes[108] = ('IL', 'Hebrew')
_langcodes[109] = ('', 'Hausa')
_langcodes[110] = ('', 'Gurani')
_langcodes[111] = ('', 'Gujarati')
_langcodes[112] = ('GR', 'Greek')
_langcodes[113] = ('GE', 'Georgian')
_langcodes[114] = ('', 'Fulani')
_langcodes[115] = ('', 'Dari')
_langcodes[116] = ('', 'Churash')
_langcodes[117] = ('CN', 'Chinese')
_langcodes[118] = ('MM', 'Burmese')
_langcodes[119] = ('BG', 'Bulgarian')
_langcodes[120] = ('BD', 'Bengali')
_langcodes[121] = ('', 'Bielorussian')
_langcodes[122] = ('', 'Bambora')
_langcodes[123] = ('', 'Azerbaijani')
_langcodes[124] = ('', 'Assamese')
_langcodes[125] = ('AM', 'Armenian')
_langcodes[126] = ('', 'Arabic')
_langcodes[127] = ('', 'Amharic')

