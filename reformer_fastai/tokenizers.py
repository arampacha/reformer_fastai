# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/05_tokenizers.ipynb (unless otherwise specified).

__all__ = ['ByteTextTokenizer', 'SubwordTextEncoder']

# Cell

import six
from six import int2byte, unichr, PY2, iterkeys, iteritems, text_type
from six.moves import range as six_range
import collections

import unicodedata
from itertools import chain

from fastai.basics import *
from fastai.text.all import *

# Cell

class ByteTextTokenizer(Transform):
    """
        Encodes each byte to an id. For 8-bit strings only. Credit to the Tensor2Tensor library
    """
    def __init__(self, is_lm=True, add_bos=False, add_eos=False):
        self.ls_lm = is_lm
        self.add_bos, self.add_eos = add_bos, add_eos
        self.pad_token, self.eos_token, self.bos_token = '<pad>', '<eos>', '<bos>',
        self.pad_token_id, self.eos_token_id, self.bos_token_id = 0,1,2
        self.reserved_toks = [self.pad_token, self.eos_token, self.bos_token]  ## self.bos_token_id
        self.reserved_tokens_bytes = [bytes(rtok, 'ascii') for rtok in self.reserved_toks]
        self.numres = len(self.reserved_toks)
        self.int2byte = int2byte

    @typedispatch
    def __call__(self, o:list, **kwargs):
        out = [c + self.numres for s in o for c in s.encode("utf-8")]
        if self.add_bos: out = [self.bos_token_id] + out
        if self.add_eos: out =  out + [self.eos_token_id]
        if self.ls_lm:return LMTensorText(out)
        else: return TensorText(out)

    @typedispatch
    def __call__(self, o:str, **kwargs):
        out = [c + self.numres for c in o.encode("utf-8")]
        if self.add_bos: out = [self.bos_token_id] + out
        if self.add_eos: out =  out + [self.eos_token_id]
        if self.ls_lm:return LMTensorText(out)
        else: return TensorText(out)

    def encodes(self,o):
        return self.__call__(o)

    def decodes(self, o:tuple):
        decoded_ids = ()
        for i in o:
            tmp_ls=[]
            for id_ in i:
                if 0 <= id_ < self.numres: tmp_ls.append(self.reserved_tokens_bytes[int(id_)])
                else: tmp_ls.append(self.int2byte(id_ - self.numres))
            decoded_ids = decoded_ids + (b"".join(tmp_ls).decode("utf-8", "replace"),)
        return TitledStr(decoded_ids)

    def decodes(self, o:list):
        decoded_ids = []
        for id_ in o:
            if 0 <= id_ < self.numres: decoded_ids.append(self.reserved_tokens_bytes[int(id_)])
            else: decoded_ids.append(self.int2byte(id_ - self.numres))
        return TitledStr(b"".join(decoded_ids).decode("utf-8", "replace"))

    def decodes(self, o:TensorText):
        return self.decodes(o.tolist())

    def decodes(self, o:LMTensorText):
        return self.decodes(o.tolist())

    @property
    def vocab_size(self): return 2**8 + self.numres

# Cell

class SubwordTextEncoder(Transform):
  """
  Class for invertibly encoding text using a limited vocabulary.

  """

  def __init__(self, filename=None, seq_len=256, ls_lm=True, add_bos=False, BOS_ID=None):
    store_attr()
    self.native_to_unicode = (lambda s: s.decode("utf-8")) if PY2 else (lambda s: s)
    self._ALPHANUMERIC_CHAR_SET = set(unichr(i) for i in six_range(sys.maxunicode) if (unicodedata.category(unichr(i)).startswith("L") or unicodedata.category(unichr(i)).startswith("N")))

    self.PAD = "<pad>"
    self.EOS = "<EOS>"
    self.RESERVED_TOKENS = [self.PAD, self.EOS]
    self.NUM_RESERVED_TOKENS = len(self.RESERVED_TOKENS)
    self.PAD_ID = self.RESERVED_TOKENS.index(self.PAD)  # Normally 0
    self.EOS_ID = self.RESERVED_TOKENS.index(self.EOS)  # Normally 1
    if BOS_ID is None: self.BOS_ID = self.PAD_ID

    self._UNESCAPE_REGEX = re.compile(r"\\u|\\\\|\\([0-9]+);")
    self._ESCAPE_CHARS = set(u"\\_u;0123456789")

    self._alphabet = set()
    self.filename = filename
    if filename is not None:
      self._load_from_file(filename)
    super(SubwordTextEncoder, self).__init__()

  def encodes(self, s):
    """Converts a native string to a list of subtoken ids.

    Args:
      s: a native string.
    Returns:
      a list of integers in the range [0, vocab_size)
    """
    return self.__call__(s)

  @typedispatch
  def __call__(self, s:str, **kwargs):
    out = self._tokens_to_subtoken_ids(self._encode(text=self.native_to_unicode(s)))
    if self.add_bos: out = [self.BOS_ID] + out[:self.seq_len-1]
    else: out = out[:self.seq_len]
    if self.ls_lm: return LMTensorText(out)
    else: return TensorText(out)

  def encode_without_tokenizing(self, token_text):
    """Converts string to list of subtoken ids without calling tokenizer.

    This treats `token_text` as a single token and directly converts it
    to subtoken ids. This may be useful when the default tokenizer doesn't
    do what we want (e.g., when encoding text with tokens composed of lots of
    nonalphanumeric characters). It is then up to the caller to make sure that
    raw text is consistently converted into tokens. Only use this if you are
    sure that `encode` doesn't suit your needs.

    Args:
      token_text: A native string representation of a single token.
    Returns:
      A list of subword token ids; i.e., integers in the range [0, vocab_size).
    """
    return self._tokens_to_subtoken_ids([self.native_to_unicode(token_text)])

  def decodes(self, ids, strip_extraneous=False):
    """Converts a sequence of subtoken ids to a native string.

    Args:
      ids: a list of integers in the range [0, vocab_size)
      strip_extraneous: bool, whether to strip off extraneous tokens
        (EOS and PAD).

    Returns:
      a native string
    """
    if strip_extraneous:
      ids = strip_ids(ids, list(six_range(self._num_reserved_ids or 0)))
    return self.unicode_to_native(
        self._decode(self._subtoken_ids_to_tokens(ids)))

  def decode_list(self, ids):
    return [self._subtoken_id_to_subtoken_string(s) for s in ids]

  @property
  def vocab_size(self):
    """The subtoken vocabulary size."""
    return len(self._all_subtoken_strings)

  def _tokens_to_subtoken_ids(self, tokens):
    """Converts a list of tokens to a list of subtoken ids.

    Args:
      tokens: a list of strings.
    Returns:
      a list of integers in the range [0, vocab_size)
    """
    ret = []
    for token in tokens:
      ret.extend(self._token_to_subtoken_ids(token))
    return ret

  def _token_to_subtoken_ids(self, token):
    """Converts token to a list of subtoken ids.

    Args:
      token: a string.
    Returns:
      a list of integers in the range [0, vocab_size)
    """
    cache_location = hash(token) % self._cache_size
    cache_key, cache_value = self._cache[cache_location]
    if cache_key == token:
      return cache_value
    ret = self._escaped_token_to_subtoken_ids(
        self._escape_token(token, self._alphabet))
    self._cache[cache_location] = (token, ret)
    return ret

  def _subtoken_ids_to_tokens(self, subtokens):
    """Converts a list of subtoken ids to a list of tokens.

    Args:
      subtokens: a list of integers in the range [0, vocab_size)
    Returns:
      a list of strings.
    """
    concatenated = "".join(
        [self._subtoken_id_to_subtoken_string(s) for s in subtokens])
    split = concatenated.split("_")
    ret = []
    for t in split:
      if t:
        unescaped = self._unescape_token(t + "_")
        if unescaped:
          ret.append(unescaped)
    return ret

  def _subtoken_id_to_subtoken_string(self, subtoken):
    """Converts a subtoken integer ID to a subtoken string."""
    if 0 <= subtoken < self.vocab_size:
      return self._all_subtoken_strings[subtoken]
    return u""

  def _escaped_token_to_subtoken_strings(self, escaped_token):
    """Converts an escaped token string to a list of subtoken strings.

    Args:
      escaped_token: An escaped token as a unicode string.
    Returns:
      A list of subtokens as unicode strings.
    """
    # NOTE: This algorithm is greedy; it won't necessarily produce the "best"
    # list of subtokens.
    ret = []
    start = 0
    token_len = len(escaped_token)
    while start < token_len:
      for end in six_range(
          min(token_len, start + self._max_subtoken_len), start, -1):
        subtoken = escaped_token[start:end]
        if subtoken in self._subtoken_string_to_id:
          ret.append(subtoken)
          start = end
          break

      else:  # Did not break
        # If there is no possible encoding of the escaped token then one of the
        # characters in the token is not in the alphabet. This should be
        # impossible and would be indicative of a bug.
        assert False, "Token substring not found in subtoken vocabulary."

    return ret

  def _escaped_token_to_subtoken_ids(self, escaped_token):
    """Converts an escaped token string to a list of subtoken IDs.

    Args:
      escaped_token: An escaped token as a unicode string.
    Returns:
      A list of subtoken IDs as integers.
    """
    return [
        self._subtoken_string_to_id[subtoken]
        for subtoken in self._escaped_token_to_subtoken_strings(escaped_token)
    ]

  @classmethod
  def build_from_generator(cls,
                           generator,
                           target_size,
                           max_subtoken_length=None,
                           reserved_tokens=None):
    """Builds a SubwordTextEncoder from the generated text.

    Args:
      generator: yields text.
      target_size: int, approximate vocabulary size to create.
      max_subtoken_length: Maximum length of a subtoken. If this is not set,
        then the runtime and memory use of creating the vocab is quadratic in
        the length of the longest token. If this is set, then it is instead
        O(max_subtoken_length * length of longest token).
      reserved_tokens: List of reserved tokens. The global variable
        `RESERVED_TOKENS` must be a prefix of `reserved_tokens`. If this
        argument is `None`, it will use `RESERVED_TOKENS`.

    Returns:
      SubwordTextEncoder with `vocab_size` approximately `target_size`.
    """
    token_counts = collections.defaultdict(int)
    for item in generator:
      for tok in self._encode(self.native_to_unicode(item)):
        token_counts[tok] += 1
    encoder = cls.build_to_target_size(
        target_size, token_counts, 1, 1e3,
        max_subtoken_length=max_subtoken_length,
        reserved_tokens=reserved_tokens)
    return encoder

  @classmethod
  def build_to_target_size(cls,
                           target_size,
                           token_counts,
                           min_val,
                           max_val,
                           max_subtoken_length=None,
                           reserved_tokens=None,
                           num_iterations=4):
    """Builds a SubwordTextEncoder that has `vocab_size` near `target_size`.

    Uses simple recursive binary search to find a minimum token count that most
    closely matches the `target_size`.

    Args:
      target_size: Desired vocab_size to approximate.
      token_counts: A dictionary of token counts, mapping string to int.
      min_val: An integer; lower bound for the minimum token count.
      max_val: An integer; upper bound for the minimum token count.
      max_subtoken_length: Maximum length of a subtoken. If this is not set,
        then the runtime and memory use of creating the vocab is quadratic in
        the length of the longest token. If this is set, then it is instead
        O(max_subtoken_length * length of longest token).
      reserved_tokens: List of reserved tokens. The global variable
        `RESERVED_TOKENS` must be a prefix of `reserved_tokens`. If this
        argument is `None`, it will use `RESERVED_TOKENS`.
      num_iterations: An integer; how many iterations of refinement.

    Returns:
      A SubwordTextEncoder instance.

    Raises:
      ValueError: If `min_val` is greater than `max_val`.
    """
    if min_val > max_val:
      raise ValueError("Lower bound for the minimum token count "
                       "is greater than the upper bound.")
    if target_size < 1:
      raise ValueError("Target size must be positive.")

    if reserved_tokens is None:
      reserved_tokens = RESERVED_TOKENS

    def bisect(min_val, max_val):
      """Bisection to find the right size."""
      present_count = (max_val + min_val) // 2
      #tf.logging.info("Trying min_count %d" % present_count)
      subtokenizer = cls()
      subtokenizer.build_from_token_counts(
          token_counts, present_count, num_iterations,
          max_subtoken_length=max_subtoken_length,
          reserved_tokens=reserved_tokens)

      # Being within 1% of the target size is ok.
      is_ok = abs(subtokenizer.vocab_size - target_size) * 100 < target_size
      # If min_val == max_val, we can't do any better than this.
      if is_ok or min_val >= max_val or present_count < 2:
        return subtokenizer

      if subtokenizer.vocab_size > target_size:
        other_subtokenizer = bisect(present_count + 1, max_val)
      else:
        other_subtokenizer = bisect(min_val, present_count - 1)

      if other_subtokenizer is None:
        return subtokenizer

      if (abs(other_subtokenizer.vocab_size - target_size) <
          abs(subtokenizer.vocab_size - target_size)):
        return other_subtokenizer
      return subtokenizer

    return bisect(min_val, max_val)

  def build_from_token_counts(self,
                              token_counts,
                              min_count,
                              num_iterations=4,
                              reserved_tokens=None,
                              max_subtoken_length=None):
    """Train a SubwordTextEncoder based on a dictionary of word counts.

    Args:
      token_counts: a dictionary of Unicode strings to int.
      min_count: an integer - discard subtokens with lower counts.
      num_iterations: an integer.  how many iterations of refinement.
      reserved_tokens: List of reserved tokens. The global variable
        `RESERVED_TOKENS` must be a prefix of `reserved_tokens`. If this
        argument is `None`, it will use `RESERVED_TOKENS`.
      max_subtoken_length: Maximum length of a subtoken. If this is not set,
        then the runtime and memory use of creating the vocab is quadratic in
        the length of the longest token. If this is set, then it is instead
        O(max_subtoken_length * length of longest token).

    Raises:
      ValueError: if reserved is not 0 or len(RESERVED_TOKENS). In this case, it
        is not clear what the space is being reserved for, or when it will be
        filled in.
    """
    if reserved_tokens is None:
      reserved_tokens = RESERVED_TOKENS
    else:
      # There is not complete freedom in replacing RESERVED_TOKENS.
      for default, proposed in zip(RESERVED_TOKENS, reserved_tokens):
        if default != proposed:
          raise ValueError("RESERVED_TOKENS must be a prefix of "
                           "reserved_tokens.")

    # Initialize the alphabet. Note, this must include reserved tokens or it can
    # result in encoding failures.
    alphabet_tokens = chain(iterkeys(token_counts),
                            [self.native_to_unicode(t) for t in reserved_tokens])

    self._init_alphabet_from_tokens(alphabet_tokens)

    # Bootstrap the initial list of subtokens with the characters from the
    # alphabet plus the escaping characters.
    self._init_subtokens_from_list(list(self._alphabet),
                                   reserved_tokens=reserved_tokens)

    # We build iteratively.  On each iteration, we segment all the words,
    # then count the resulting potential subtokens, keeping the ones
    # with high enough counts for our new vocabulary.
    if min_count < 1:
      min_count = 1
    for i in six_range(num_iterations):
      #tf.logging.info("Iteration {0}".format(i))

      # Collect all substrings of the encoded token that break along current
      # subtoken boundaries.
      subtoken_counts = collections.defaultdict(int)
      for token, count in iteritems(token_counts):
        iter_start_time = time.time()
        escaped_token = self._escape_token(token, self._alphabet)
        subtokens = self._escaped_token_to_subtoken_strings(escaped_token)
        start = 0
        for subtoken in subtokens:
          last_position = len(escaped_token) + 1
          if max_subtoken_length is not None:
            last_position = min(last_position, start + max_subtoken_length)

          for end in six_range(start + 1, last_position):
            new_subtoken = escaped_token[start:end]
            subtoken_counts[new_subtoken] += count
          start += len(subtoken)
        iter_time_secs = time.time() - iter_start_time
        if iter_time_secs > 0.1:
          print(u"Processing token [{0}] took {1} seconds, consider "
                          "setting Text2TextProblem.max_subtoken_length to a "
                          "smaller value.".format(token, iter_time_secs))

      # Array of sets of candidate subtoken strings, by length.
      len_to_subtoken_strings = []
      for subtoken_string, count in iteritems(subtoken_counts):
        lsub = len(subtoken_string)
        if count >= min_count:
          while len(len_to_subtoken_strings) <= lsub:
            len_to_subtoken_strings.append(set())
          len_to_subtoken_strings[lsub].add(subtoken_string)

      # Consider the candidates longest to shortest, so that if we accept
      # a longer subtoken string, we can decrement the counts of its prefixes.
      new_subtoken_strings = []
      for lsub in six_range(len(len_to_subtoken_strings) - 1, 0, -1):
        subtoken_strings = len_to_subtoken_strings[lsub]
        for subtoken_string in subtoken_strings:
          count = subtoken_counts[subtoken_string]
          if count >= min_count:
            # Exclude alphabet tokens here, as they must be included later,
            # explicitly, regardless of count.
            if subtoken_string not in self._alphabet:
              new_subtoken_strings.append((count, subtoken_string))
            for l in six_range(1, lsub):
              subtoken_counts[subtoken_string[:l]] -= count

      # Include the alphabet explicitly to guarantee all strings are encodable.
      new_subtoken_strings.extend((subtoken_counts.get(a, 0), a)
                                  for a in self._alphabet)
      new_subtoken_strings.sort(reverse=True)

      # Reinitialize to the candidate vocabulary.
      new_subtoken_strings = [subtoken for _, subtoken in new_subtoken_strings]
      if reserved_tokens:
        escaped_reserved_tokens = [
            self._escape_token(self.native_to_unicode(t), self._alphabet)
            for t in reserved_tokens
        ]
        new_subtoken_strings = escaped_reserved_tokens + new_subtoken_strings

      self._init_subtokens_from_list(new_subtoken_strings)
      #tf.logging.info("vocab_size = %d" % self.vocab_size)

  @property
  def all_subtoken_strings(self):
    return tuple(self._all_subtoken_strings)

  def dump(self):
    """Debugging dump of the current subtoken vocabulary."""
    subtoken_strings = [(i, s)
                        for s, i in iteritems(self._subtoken_string_to_id)]
    print(u", ".join(u"{0} : '{1}'".format(i, s)
                     for i, s in sorted(subtoken_strings)))

  def _init_subtokens_from_list(self, subtoken_strings, reserved_tokens=None):
    """Initialize token information from a list of subtoken strings.

    Args:
      subtoken_strings: a list of subtokens
      reserved_tokens: List of reserved tokens. We must have `reserved_tokens`
        as None or the empty list, or else the global variable `RESERVED_TOKENS`
        must be a prefix of `reserved_tokens`.

    Raises:
      ValueError: if reserved is not 0 or len(RESERVED_TOKENS). In this case, it
        is not clear what the space is being reserved for, or when it will be
        filled in.
    """
    if reserved_tokens is None:
      reserved_tokens = []

    if reserved_tokens:
      self._all_subtoken_strings = reserved_tokens + subtoken_strings
    else:
      self._all_subtoken_strings = subtoken_strings

    # we remember the maximum length of any subtoken to avoid having to
    # check arbitrarily long strings.
    self._max_subtoken_len = max([len(s) for s in subtoken_strings])
    self._subtoken_string_to_id = {
        s: i + len(reserved_tokens)
        for i, s in enumerate(subtoken_strings) if s
    }
    # Initialize the cache to empty.
    self._cache_size = 2 ** 20
    self._cache = [(None, None)] * self._cache_size

  def _init_alphabet_from_tokens(self, tokens):
    """Initialize alphabet from an iterable of token or subtoken strings."""
    # Include all characters from all tokens in the alphabet to guarantee that
    # any token can be encoded. Additionally, include all escaping characters.
    self._alphabet = {c for token in tokens for c in token}
    self._alphabet |= self._ESCAPE_CHARS

  def _load_from_file_object(self, f):
    """Load from a file object.

    Args:
      f: File object to load vocabulary from
    """
    subtoken_strings = []
    for line in f:
      s = line.rstrip()
      # Some vocab files wrap words in single quotes, but others don't
      if ((s.startswith("'") and s.endswith("'")) or
          (s.startswith("\"") and s.endswith("\""))):
        s = s[1:-1]
      subtoken_strings.append(self.native_to_unicode(s))
    self._init_subtokens_from_list(subtoken_strings)
    self._init_alphabet_from_tokens(subtoken_strings)

  def _load_from_file(self, filename):
    """Load from a vocab file."""
    if not Path(filename).exists():
      raise ValueError("File %s not found" % filename)
    with Path(filename).open() as f:
      self._load_from_file_object(f)

  def store_to_file(self, filename, add_single_quotes=True):
    with Path(filename).open('w') as f:
      for subtoken_string in self._all_subtoken_strings:
        if add_single_quotes:
          f.write("'" + self.unicode_to_native(subtoken_string) + "'\n")
        else:
          f.write(self.unicode_to_native(subtoken_string) + "\n")
		
  def unicode_to_native(self,s):
    if PY2:
      return s.encode("utf-8") if is_unicode(s) else s
    else:
      return s

  def _escape_token(self,token, alphabet):
    if not isinstance(token, text_type):
      raise ValueError("Expected string type for token, got %s" % type(token))

    token = token.replace(u"\\", u"\\\\").replace(u"_", u"\\u")
    ret = [c if c in alphabet and c != u"\n" else r"\%d;" % ord(c) for c in token]
    return u"".join(ret) + "_"


  def _unescape_token(self,escaped_token):
    def match(m):
      if m.group(1) is None:
        return u"_" if m.group(0) == u"\\u" else u"\\"

      try:
        return unichr(int(m.group(1)))
      except (ValueError, OverflowError) as _:
        return u"\u3013"  # Unicode for undefined character.

    trimmed = escaped_token[:-1] if escaped_token.endswith("_") else escaped_token
    return self._UNESCAPE_REGEX.sub(match, trimmed)

  def _encode(self,text):
    if not text:
      return []
    ret = []
    token_start = 0
    # Classify each character in the input string
    is_alnum = [c in self._ALPHANUMERIC_CHAR_SET for c in text]
    for pos in six_range(1, len(text)):
      if is_alnum[pos] != is_alnum[pos - 1]:
        token = text[token_start:pos]
        if token != u" " or token_start == 0:
          ret.append(token)
        token_start = pos
    final_token = text[token_start:]
    ret.append(final_token)
    return ret

  def _decode(self,tokens):
    token_is_alnum = [t[0] in self._ALPHANUMERIC_CHAR_SET for t in tokens]
    ret = []
    for i, token in enumerate(tokens):
      if i > 0 and token_is_alnum[i - 1] and token_is_alnum[i]:
        ret.append(u" ")
      ret.append(token)
    return TitledStr("".join(ret))