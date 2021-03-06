# -*- coding: utf-8 -*-

"""
Implementation of PyConvResNet
"""

import sys
import logging
from torchvision.models.utils import load_state_dict_from_url
from holocron.nn import PyConv2d
from .resnet import ResNet, _ResBlock
from .utils import conv_sequence


__all__ = ['PyBottleneck', 'pyconv_resnet50', 'pyconvhg_resnet50']


default_cfgs = {
    'pyconv_resnet50': {'block': 'PyBottleneck', 'num_blocks': [3, 4, 6, 3], 'out_chans': [64, 128, 256, 512],
                        'width_per_group': 64,
                        'groups': [[1, 4, 8, 16], [1, 4, 8], [1, 4], [1]],
                        'url': None},
    'pyconvhg_resnet50': {'block': 'PyHGBottleneck', 'num_blocks': [3, 4, 6, 3], 'out_chans': [128, 256, 512, 1024],
                          'width_per_group': 2,
                          'groups': [[32, 32, 32, 32], [32, 64, 64], [32, 64], [32]],
                          'url': None},
}


class PyBottleneck(_ResBlock):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None, groups=None, base_width=64, dilation=1,
                 act_layer=None, norm_layer=None, drop_layer=None, num_levels=2, **kwargs):

        width = int(planes * (base_width / 64.)) * min(groups)

        super().__init__(
            [*conv_sequence(inplanes, width, act_layer, norm_layer, drop_layer, kernel_size=1,
                            stride=1, bias=False, **kwargs),
             *conv_sequence(width, width, act_layer, norm_layer, drop_layer, conv_layer=PyConv2d, kernel_size=3,
                            stride=stride, padding=dilation, groups=groups, bias=False, dilation=dilation,
                            num_levels=num_levels, **kwargs),
             *conv_sequence(width, planes * self.expansion, None, norm_layer, drop_layer, kernel_size=1,
                            stride=1, bias=False, **kwargs)],
            downsample, act_layer)


class PyHGBottleneck(PyBottleneck):
    expansion = 2


def _pyconvresnet(arch, pretrained, progress, **kwargs):

    # Retrieve the correct block type
    block = sys.modules[__name__].__dict__[default_cfgs[arch]['block']]
    # Build the model
    model = ResNet(block, default_cfgs[arch]['num_blocks'], default_cfgs[arch]['out_chans'], stem_pool=False,
                   width_per_group=default_cfgs[arch]['width_per_group'],
                   block_args=[dict(num_levels=len(group), groups=group)
                               for group in default_cfgs[arch]['groups']], **kwargs)
    # Load pretrained parameters
    if pretrained:
        if default_cfgs[arch]['url'] is None:
            logging.warning(f"Invalid model URL for {arch}, using default initialization.")
        else:
            state_dict = load_state_dict_from_url(default_cfgs[arch]['url'],
                                                  progress=progress)
            model.load_state_dict(state_dict)

    return model


def pyconv_resnet50(pretrained=False, progress=True, **kwargs):
    """PyConvResNet-50 from `"Pyramidal Convolution: Rethinking Convolutional Neural Networks
    for Visual Recognition" <https://arxiv.org/pdf/2006.11538.pdf>`_

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr

    Returns:
        torch.nn.Module: classification model
    """

    return _pyconvresnet('pyconv_resnet50', pretrained, progress, **kwargs)


def pyconvhg_resnet50(pretrained=False, progress=True, **kwargs):
    """PyConvHGResNet-50 from `"Pyramidal Convolution: Rethinking Convolutional Neural Networks
    for Visual Recognition" <https://arxiv.org/pdf/2006.11538.pdf>`_

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
        progress (bool): If True, displays a progress bar of the download to stderr

    Returns:
        torch.nn.Module: classification model
    """

    return _pyconvresnet('pyconvhg_resnet50', pretrained, progress, **kwargs)
