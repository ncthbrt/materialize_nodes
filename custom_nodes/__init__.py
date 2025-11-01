# SPDX-FileCopyrightText: 2025 Natalie Cuthbert <natalie@cuthbert.co.za>
# SPDX-FileCopyrightText: 2025 BD3D DIGITAL DESIGN (Dorian B.)
# SPDX-License-Identifier: GPL-3.0-or-later

GN_CustomNodes = ("Armature", ())

classes = (+GN_CustomNodes)

#for utility. handlers.py module will use this list.
allcustomnodes = tuple(cls for cls in classes if (('_NG_' in cls.__name__) or ('_ND_' in cls.__name__)))
