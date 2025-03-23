from contextlib import contextmanager, nullcontext
from typing import Iterator, Union
import torch

@contextmanager
def autocast_exclude_mps(
    device_type: str, enabled: bool = True, **kwargs
) -> Iterator[Union[nullcontext[None], torch.autocast]]:
    """
    Context manager for autocast that excludes MPS devices.
    """
    if device_type == "mps":
        yield nullcontext()
    else:
        yield torch.autocast(device_type=device_type, enabled=enabled, **kwargs)
