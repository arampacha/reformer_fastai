# Implementation Notes

## Finding the enwik8 version used in Reformer paper

The enwik9 dataset used in the Reformer paper used a Tensor2Tensor dataset that does the encoding (via `ByteTextEncoder`)

Tracking down the encoding used:

### Trax `tf_inputs`:
In the Reformer enwik8 config `tf_inputs` is called to handle the data streams

tf_inputs:
https://github.com/google/trax/blob/f8024e8057599b92fce82842f342cb3d39c8f405/trax/data/tf_inputs.py#L265

Within `tf_inputs`, `_train_and_eval_dataset_v1` is used to call the `t2t_enwik8_l65k` dataset ("t2t_enwik8_l65k" is named in the Reformer config)

### `Enwik8L65k` dataset
The `t2t_enwik8_l65k` string maps to the `Enwik8L65k` dataset Tensor2Tensor "Problem" (https://github.com/tensorflow/tensor2tensor/blob/master/tensor2tensor/data_generators/enwik8.py). 

`Enwik8L65k` subclasses `Text2SelfProblem` which subclasses `Text2TextProblem` in `text_problems.py`.

### `Text2TextProblem` Problem class

`Text2TextProblem` calls `text_encoder.ByteTextEncoder()`

`Text2TextProblem` is defined in `text_problems.py`: https://github.com/tensorflow/tensor2tensor/blob/5f9dd2db6d7797162e53adf152310ed13e9fc711/tensor2tensor/data_generators/text_problems.py#L53

### `ByteTextEncoder` Text Encoder

`ByteTextEncoder` is defined in `text_encoder.py`

https://github.com/tensorflow/tensor2tensor/blob/5f9dd2db6d7797162e53adf152310ed13e9fc711/tensor2tensor/data_generators/text_encoder.py#L176

`ByteTextEncoder` defined as:

```
class ByteTextEncoder(TextEncoder):
  """Encodes each byte to an id. For 8-bit strings only."""

  def encode(self, s):
    numres = self._num_reserved_ids
    if six.PY2:
      if isinstance(s, unicode):
        s = s.encode("utf-8")
      return [ord(c) + numres for c in s]
    # Python3: explicitly convert to UTF-8
    return [c + numres for c in s.encode("utf-8")]

  def decode(self, ids, strip_extraneous=False):
    if strip_extraneous:
      ids = strip_ids(ids, list(range(self._num_reserved_ids or 0)))
    numres = self._num_reserved_ids
    decoded_ids = []
    int2byte = six.int2byte
    for id_ in ids:
      if 0 <= id_ < numres:
        decoded_ids.append(RESERVED_TOKENS_BYTES[int(id_)])
      else:
        decoded_ids.append(int2byte(id_ - numres))
    if six.PY2:
      return "".join(decoded_ids)
    # Python3: join byte arrays and then decode string
    return b"".join(decoded_ids).decode("utf-8", "replace")

  def decode_list(self, ids):
    numres = self._num_reserved_ids
    decoded_ids = []
    int2byte = six.int2byte
    for id_ in ids:
      if 0 <= id_ < numres:
        decoded_ids.append(RESERVED_TOKENS_BYTES[int(id_)])
      else:
        decoded_ids.append(int2byte(id_ - numres))
    # Python3: join byte arrays and then decode string
    return decoded_ids

  @property
  def vocab_size(self):
    return 2**8 + self._num_reserved_ids

```
