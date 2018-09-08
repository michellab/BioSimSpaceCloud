

from ._debitnote import DebitNote as _DebitNote
from ._creditnote import CreditNote as _CreditNote

__all__ = ["PairedNote"]


class PairedNote:
    """This class holds a DebitNote together with its matching
       CreditNote(s)
    """
    def __init__(self, debit_note, credit_note):
        """Construct from the matching pair of notes"""
        if credit_note.uid() != debit_note.uid():
            raise ValueError("You must pair up DebitNote (%s) with a "
                             "matching CreditNote (%s)" %
                             (debit_note.uid(), credit_note.uid()))

        self._debit_note = debit_note
        self._credit_note = credit_note

    @staticmethod
    def create(debit_notes, credit_notes):
        """Return a list of PairedNotes that pair together the passed
           debit notes and credit notes
        """

        try:
            debit_note = debit_notes[0]
        except:
            SOMETHONG