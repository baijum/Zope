# Authors: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.2 $
# Date: $Date: 2003/02/01 09:26:20 $
# Copyright: This module has been placed in the public domain.

"""
Simple internal document tree Writer, writes Docutils XML.
"""

__docformat__ = 'reStructuredText'


import docutils
from docutils import writers


class Writer(writers.Writer):

    supported = ('xml',)
    """Formats this writer supports."""

    settings_spec = (
        '"Docutils XML" Writer Options',
        'Warning: the --newlines and --indents options may adversely affect '
        'whitespace; use them only for reading convenience.',
        (('Generate XML with newlines before and after tags.',
          ['--newlines'], {'action': 'store_true'}),
         ('Generate XML with indents and newlines.',
          ['--indents'], {'action': 'store_true'}),
         ('Omit the XML declaration.  Use with caution.',
          ['--no-xml-declaration'], {'dest': 'xml_declaration', 'default': 1,
                                     'action': 'store_false'}),
         ('Omit the DOCTYPE declaration.',
          ['--no-doctype'], {'dest': 'doctype_declaration', 'default': 1,
                             'action': 'store_false'}),))

    output = None
    """Final translated form of `document`."""

    xml_declaration = '<?xml version="1.0" encoding="%s"?>\n'
    #xml_stylesheet = '<?xml-stylesheet type="text/xsl" href="%s"?>\n'
    doctype = (
        '<!DOCTYPE document PUBLIC'
        ' "+//IDN docutils.sourceforge.net//DTD Docutils Generic//EN//XML"'
        ' "http://docutils.sourceforge.net/spec/docutils.dtd">\n')
    generator = '<!-- Generated by Docutils %s -->\n'

    def translate(self):
        settings = self.document.settings
        indent = newline = ''
        if settings.newlines:
            newline = '\n'
        if settings.indents:
            newline = '\n'
            indent = '    '
        output_prefix = []
        if settings.xml_declaration:
            output_prefix.append(
                self.xml_declaration % settings.output_encoding)
        if settings.doctype_declaration:
            output_prefix.append(self.doctype)
        output_prefix.append(self.generator % docutils.__version__)
        docnode = self.document.asdom().childNodes[0]
        self.output = (''.join(output_prefix)
                       + docnode.toprettyxml(indent, newline))
