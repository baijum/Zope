# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.2.10.7 $
# Date: $Date: 2005/01/07 13:26:04 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/docs/howto/i18n.html>.  Two files must be
# translated for each language: one in docutils/languages, the other in
# docutils/parsers/rst/languages.

"""
English-language mappings for language-dependent features of
reStructuredText.
"""

__docformat__ = 'reStructuredText'


directives = {
      # language-dependent: fixed
      'attention': 'attention',
      'caution': 'caution',
      'danger': 'danger',
      'error': 'error',
      'hint': 'hint',
      'important': 'important',
      'note': 'note',
      'tip': 'tip',
      'warning': 'warning',
      'admonition': 'admonition',
      'sidebar': 'sidebar',
      'topic': 'topic',
      'line-block': 'line-block',
      'parsed-literal': 'parsed-literal',
      'rubric': 'rubric',
      'epigraph': 'epigraph',
      'highlights': 'highlights',
      'pull-quote': 'pull-quote',
      'compound': 'compound',
      #'questions': 'questions',
      'table': 'table',
      'csv-table': 'csv-table',
      #'qa': 'questions',
      #'faq': 'questions',
      'meta': 'meta',
      #'imagemap': 'imagemap',
      'image': 'image',
      'figure': 'figure',
      'include': 'include',
      'raw': 'raw',
      'replace': 'replace',
      'unicode': 'unicode',
      'class': 'class',
      'role': 'role',
      'contents': 'contents',
      'sectnum': 'sectnum',
      'section-numbering': 'sectnum',
      #'footnotes': 'footnotes',
      #'citations': 'citations',
      'target-notes': 'target-notes',
      'restructuredtext-test-directive': 'restructuredtext-test-directive'}
"""English name to registered (in directives/__init__.py) directive name
mapping."""

roles = {
    # language-dependent: fixed
    'abbreviation': 'abbreviation',
    'ab': 'abbreviation',
    'acronym': 'acronym',
    'ac': 'acronym',
    'index': 'index',
    'i': 'index',
    'subscript': 'subscript',
    'sub': 'subscript',
    'superscript': 'superscript',
    'sup': 'superscript',
    'title-reference': 'title-reference',
    'title': 'title-reference',
    't': 'title-reference',
    'pep-reference': 'pep-reference',
    'pep': 'pep-reference',
    'rfc-reference': 'rfc-reference',
    'rfc': 'rfc-reference',
    'emphasis': 'emphasis',
    'strong': 'strong',
    'literal': 'literal',
    'named-reference': 'named-reference',
    'anonymous-reference': 'anonymous-reference',
    'footnote-reference': 'footnote-reference',
    'citation-reference': 'citation-reference',
    'substitution-reference': 'substitution-reference',
    'target': 'target',
    'uri-reference': 'uri-reference',
    'uri': 'uri-reference',
    'url': 'uri-reference',
    'raw': 'raw',}
"""Mapping of English role names to canonical role names for interpreted text.
"""
