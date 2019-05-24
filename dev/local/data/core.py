#AUTOGENERATED! DO NOT EDIT! File to edit: dev/04_data_core.ipynb (unless otherwise specified).

__all__ = ['get_files', 'FileGetter', 'image_extensions', 'get_image_files', 'ImageGetter', 'RandomSplitter',
           'GrandparentSplitter', 'parent_label', 'RegexLabeller', 'show_image', 'show_title', 'show_image_batch',
           'TfmDataLoader', 'DataBunch']

from ..imports import *
from ..test import *
from ..core import *
from .pipeline import *
from .external import *
from ..notebook.showdoc import show_doc

def _get_files(p, fs, extensions=None):
    p = Path(p)
    res = [p/f for f in fs if not f.startswith('.')
           and ((not extensions) or f'.{f.split(".")[-1].lower()}' in extensions)]
    return res

def get_files(path, extensions=None, recurse=True, include=None):
    "Get all the files in `path` with optional `extensions`, optionally with `recurse`."
    path = Path(path)
    extensions = setify(extensions)
    extensions = {e.lower() for e in extensions}
    if recurse:
        res = []
        for i,(p,d,f) in enumerate(os.walk(path)): # returns (dirpath, dirnames, filenames)
            if include is not None and i==0: d[:] = [o for o in d if o in include]
            else:                            d[:] = [o for o in d if not o.startswith('.')]
            res += _get_files(p, f, extensions)
    else:
        f = [o.name for o in os.scandir(path) if o.is_file()]
        res = _get_files(path, f, extensions)
    return ListContainer(res)

def FileGetter(suf='', extensions=None, recurse=True, include=None):
    "Create `get_files` partial function that searches path suffix `suf` and passes along args"
    def _inner(o, extensions=extensions, recurse=recurse, include=include): return get_files(o/suf, extensions, recurse, include)
    return _inner

image_extensions = set(k for k,v in mimetypes.types_map.items() if v.startswith('image/'))

def get_image_files(path, recurse=True, include=None):
    "Get image files in `path` recursively."
    return get_files(path, extensions=image_extensions, recurse=recurse, include=include)

def ImageGetter(suf='', recurse=True, include=None):
    "Create `get_image_files` partial function that searches path suffix `suf` and passes along `kwargs`"
    def _inner(o, recurse=recurse, include=include): return get_image_files(o/suf, recurse, include)
    return _inner

def RandomSplitter(valid_pct=0.2, seed=None, **kwargs):
    "Create function that splits `items` between train/val with `valid_pct` randomly."
    def _inner(o, **kwargs):
        if seed is not None: torch.manual_seed(seed)
        rand_idx = ListContainer(int(i) for i in torch.randperm(len(o)))
        cut = int(valid_pct * len(o))
        return rand_idx[cut:],rand_idx[:cut]
    return _inner

def _grandparent_idxs(items, name): return mask2idxs(Path(o).parent.parent.name == name for o in items)

def GrandparentSplitter(train_name='train', valid_name='valid'):
    "Split `items` from the grand parent folder names (`train_name` and `valid_name`)."
    def _inner(o, **kwargs):
        return _grandparent_idxs(o, train_name),_grandparent_idxs(o, valid_name)
    return _inner

def parent_label(o, **kwargs):
    "Label `item` with the parent folder name."
    return o.parent.name if isinstance(o, Path) else o.split(os.path.sep)[-1]

def RegexLabeller(pat):
    "Label `item` with regex `pat`."
    pat = re.compile(pat)
    def _inner(o, **kwargs):
        res = pat.search(str(o))
        assert res,f'Failed to find "{pat}" in "{o}"'
        return res.group(1)
    return _inner

def show_image(im, ax=None, figsize=None, title=None, **kwargs):
    "Show a PIL image on `ax`."
    if ax is None: _,ax = plt.subplots(figsize=figsize)
    if isinstance(im,Tensor) and im.shape[0]<5: im=im.permute(1,2,0)
    ax.imshow(im, **kwargs)
    if title is not None: ax.set_title(title)
    ax.axis('off')
    return ax

def show_title(o, ax=None):
    "Set title of `ax` to `o`, or print `o` if `ax` is `None`"
    if ax is None: print(o)
    else: ax.set_title(o)

def _show_batch_item(o,ax): show_image(o[0], ax, title=o[1])

def show_image_batch(b, show=_show_batch_item, items=9, cols=3, figsize=None, **kwargs):
    "Display batch `b` in a grid of size `items` with `cols` width"
    rows = (items+cols-1) // cols
    if figsize is None: figsize = (cols*3, rows*3)
    fig,axs = plt.subplots(rows, cols, figsize=figsize)
    for *o,ax in zip(*b, axs.flatten()): show(o, ax=ax, **kwargs)

def _DataLoader__getattr(self,k):
    try: return getattr(self.dataset, k)
    except AttributeError: raise AttributeError(k) from None
DataLoader.__getattr__ = _DataLoader__getattr

@docs
class TfmDataLoader():
    "Transformed `DataLoader` using a `Pipeline` of `tfms`"
    def __init__(self, dl, tfms=None, **kwargs):
        self.dl,self.tfm = dl,Pipeline(tfms)
        for k,v in kwargs.items(): setattr(self,k,v)

    def __len__(self): return len(self.dl)
    def __dir__(self): return custom_dir(self, 'batchsize num_workers dataset sampler pin_memory'.split())
    def __iter__(self): return map(self.tfm, self.dl)
    def decode(self, o): return self.tfm.decode(o)
    def one_batch(self): return next(iter(self))
    def decode_batch(self): return self.decode(self.one_batch())

    def __getattr__(self, k):
        try: return getattr(self.dl, k)
        except AttributeError: raise AttributeError(k) from None

    _docs = dict(decode="Decode `o` using `tfm`",
                 one_batch="Grab first batch of `dl`",
                 decode_batch="Decoded first batch of `dl`")

class DataBunch():
    "Basic wrapper around several `DataLoader`s."
    def __init__(self, *dls): self.dls = dls
    def __getitem__(self, i): return self.dls[i]

DataBunch.train_dl,DataBunch.valid_dl = add_props(lambda i,x: x[i]        , 2)
DataBunch.train_ds,DataBunch.valid_ds = add_props(lambda i,x: x[i].dataset, 2)