import pytest
from vocab2anki import __version__
from vocab2anki.vocab2anki import Anki


def test_version():
    assert __version__ == "0.1.0"


class TestAnki:
    def test_send_request(self):
        anki = Anki()

        # Sample request
        assert len(anki.send_request("deckNames")) > 0

        # Bad action
        with pytest.raises(RuntimeError) as e:
            anki.send_request("wrong_action")

        # Bad parameters
        with pytest.raises(RuntimeError) as e:
            anki.send_request("getDeckConfig")

    def test_list_decks(self):
        anki = Anki()
        assert anki.list_decks() == anki.send_request("deckNames")

    def test_create_deck(self):
        anki = Anki()
        deck_name = "test2"

        # Standard creation
        anki.create_deck(deck_name)
        assert deck_name in anki.list_decks()

        # Trying to add already existing
        prev_deck_count = len(anki.list_decks())
        anki.create_deck(deck_name)
        assert len(anki.list_decks()) == prev_deck_count

        # Cleanup
        anki.delete_deck(deck_name)

    def test_delete_deck(self):
        anki = Anki()
        deck_name = "test2"

        # Standard deletion
        anki.create_deck(deck_name)
        anki.delete_deck(deck_name)
        assert deck_name not in anki.list_decks()

        # Trying to delete already deleted
        anki.delete_deck(deck_name)

    def test_add_note(self):
        anki = Anki()
        deck_to_add_to = anki.list_decks()[0]

        # Standard note addition
        note_id = anki.add_note(deck_to_add_to, "Basic", {"Front": "test"})
        assert note_id in anki.send_request("findNotes", query="deck:" + deck_to_add_to)
        # Cleanup
        anki.send_request("deleteNotes", notes=[note_id])

        # Adding notes to a non-existing deck
        deck_name = "test1234"
        assert deck_name not in anki.list_decks()
        with pytest.raises(RuntimeError):
            note_id = anki.add_note(deck_name, "Basic", {"Front": "test"})

        # Adding notes of a non-existing type
        with pytest.raises(RuntimeError):
            note_id = anki.add_note(deck_to_add_to, "test1234", {"Front": "test"})

        # Adding notes with an empty field
        with pytest.raises(RuntimeError):
            note_id = anki.add_note(deck_to_add_to, "Basic", {"Front": ""})

    def test_add_multiple_notes(self):
        anki = Anki()
        deck_to_add_to = anki.list_decks()[0]

        # Adding notes with different fields
        prev_note_count = len(
            anki.send_request("findNotes", query="deck:" + deck_to_add_to)
        )
        with pytest.raises(RuntimeError):
            anki.add_multiple_notes(
                deck_to_add_to, "Basic", [{"Front": "tmp"}, {"test1234": "tmp1"}]
            )
        assert (
            len(anki.send_request("findNotes", query="deck:" + deck_to_add_to))
            == prev_note_count
        )
