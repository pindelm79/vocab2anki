import json
import sqlite3
from urllib.request import urlopen, Request
from urllib.error import URLError


class Anki:
    """Class representing your local Anki instance."""

    def __init__(self, version=6):
        self.version = version

    def create_deck(self, deck_name):
        """Creates a new deck with the specified name."""
        response = self.send_request("createDeck", deck=deck_name)
        print(f"Created deck {deck_name}.")
        return response

    def list_decks(self):
        """Returns a list of all decks."""
        response = self.send_request("deckNames")
        return response

    def delete_deck(self, deck_name, delete_cards=True):
        """Deletes a deck with the specified name."""
        response = self.send_request(
            "deleteDecks", decks=[deck_name], cardsToo=delete_cards
        )
        print(f"Deleted deck {deck_name}")
        return response

    def add_note(self, deck_name, note_type, fields, tags=[], allow_duplicates=True):
        """Creates a note, given a deck name, note type, field values and tags."""
        note_params = {
            "deckName": deck_name,
            "modelName": note_type,
            "fields": fields,
            "options": {"allowDuplicate": allow_duplicates},
            "tags": tags,
        }
        response = self.send_request("addNote", note=note_params)
        return response

    def add_multiple_notes(
        self, deck_name, note_type, fields_list, tags=[], allow_duplicates=True
    ):
        """An interface to the add_note function to create multiple notes in the same deck."""
        print("Adding notes...")
        for fields in fields_list:
            self.add_note(deck_name, note_type, fields, tags)
        print(f"Added {len(fields_list)} words to {deck_name}.")

    def send_request(self, action, **params):
        """Sends a specified request to the AnkiConnect API and gets the results."""
        # Creating and sending the request
        request_json = json.dumps(
            {"action": action, "params": params, "version": self.version}
        )
        response = None
        try:
            response = json.load(
                urlopen(Request("http://localhost:8765", request_json.encode("utf-8")))
            )
        except URLError as e:
            print(
                "Couldn't connect to Anki. Please make sure you have Anki opened and the AnkiConnect addon installed."
            )
            quit()

        # Error handling
        if len(response) != 2:
            raise RuntimeError("Response has an unexpected number of fields.")
        if "error" not in response:
            raise RuntimeError("Response is missing required error field.")
        if "result" not in response:
            raise RuntimeError("Response is missing required result field")
        if response["error"] is not None:
            raise RuntimeError(response["error"])

        return response["result"]


class Vocab:
    """Class representing the Vocabulary Builder from Kindle."""

    def __init__(self, path="/Volumes/Kindle/system/vocabulary/vocab.db"):
        self.connect_db(path)

    def connect_db(self, path):
        try:
            self.conn = sqlite3.connect(path)
        except sqlite3.DatabaseError as e:
            print(
                "Couldn't connect to Vocabulary Builder. Make sure your Kindle is connected."
            )
            quit()

    def import_all_words(self):
        """Imports all unmastered words and their usage into a list of dictionaries."""
        statement = """
        SELECT stem, usage
        FROM WORDS AS w JOIN LOOKUPS AS l ON w.id = l.word_key
        WHERE w.category = 0"""
        words = []
        cursor = self.conn.cursor()
        cursor.execute(statement)
        for row in cursor.fetchall():
            word = {"word": row[0], "usage": row[1]}
            words.append(word)
        cursor.close()
        return words


def main():
    anki = Anki()

    # User interaction
    deck_name = input("Target deck name: ")
    if deck_name not in anki.list_decks():
        anki.create_deck(deck_name)
    note_type = input("Target note type: ")
    word_field = input("Field to assign the actual words to: ")
    usage_field = input("Field to assign the context of the words to: ")
    tags = input("Tags (separated by spaces): ").split()
    tags.append("auto-generated")

    vocab = Vocab()
    words = vocab.import_all_words()

    fields_list = []
    for word in words:
        fields_list.append({word_field: word["word"], usage_field: word["usage"]})

    try:
        anki.add_multiple_notes(deck_name, note_type, fields_list, tags)
    except RuntimeError as e:
        print(f"Couldn't add notes. Error: {e}")


if __name__ == "__main__":
    main()
