# Author: Nicola Larosa
# Contact: docutils@tekNico.net
# Revision: $Revision: 1.5 $
# Date: $Date: 2003/11/30 15:06:05 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/spec/howto/i18n.html>.  Two files must be
# translated for each language: one in docutils/languages, the other in
# docutils/parsers/rst/languages.

"""
Italian-language mappings for language-dependent features of Docutils.
"""

__docformat__ = 'reStructuredText'

labels = {
      'author': 'Autore',
      'authors': 'Autori',
      'organization': 'Organizzazione',
      'address': 'Indirizzo',
      'contact': 'Contatti',
      'version': 'Versione',
      'revision': 'Revisione',
      'status': 'Status',
      'date': 'Data',
      'copyright': 'Copyright',
      'dedication': 'Dedica',
      'abstract': 'Riassunto',
      'attention': 'Attenzione!',
      'caution': 'Cautela!',
      'danger': '!PERICOLO!',
      'error': 'Errore',
      'hint': 'Suggerimento',
      'important': 'Importante',
      'note': 'Nota',
      'tip': 'Consiglio',
      'warning': 'Avvertenza',
      'contents': 'Indice'}
"""Mapping of node class name to label text."""

bibliographic_fields = {
      'autore': 'author',
      'autori': 'authors',
      'organizzazione': 'organization',
      'indirizzo': 'address',
      'contatti': 'contact',
      'versione': 'version',
      'revisione': 'revision',
      'status': 'status',
      'data': 'date',
      'copyright': 'copyright',
      'dedica': 'dedication',
      'riassunto': 'abstract'}
"""Italian (lowcased) to canonical name mapping for bibliographic fields."""

author_separators = [';', ',']
"""List of separator strings for the 'Authors' bibliographic field. Tried in
order."""
