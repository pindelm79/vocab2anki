import json
import sqlite3
from typing import Dict, List, Any
from urllib.request import urlopen, Request
from urllib.error import URLError


class Anki:
    """The local Anki instance."""

    def __init__(self, version: int = 6):
        self.version = version

    def create_deck(self, deck_name: str) -> int:
        """Creates a new, empty deck.

        Does not override existing decks. If a new deck was created, prints out a notification.

        Args:
            deck_name: Name of the deck to be created.

        Returns:
            ID of the created deck.
        """
        already_exists = deck_name in self.list_decks
        response = self.send_request("createDeck", deck=deck_name)
        if not already_exists:
            print(f"Created deck {deck_name}.")
        return response

    def list_decks(self) -> List[str]:
        """Returns a list of all decks."""
        response = self.send_request("deckNames")
        return response

    def delete_deck(self, deck_name: str, delete_cards: bool = True) -> None:
        """Deletes the specified deck.

        Args:
            deck_name: Name of the deck to be deleted.
            delete_cards: Whether to delete the cards in the deck (True) or move them to the Default deck (False).
        """
        response = self.send_request(
            "deleteDecks", decks=[deck_name], cardsToo=delete_cards
        )
        print(f"Deleted deck {deck_name}")
        return response

    def add_note(
        self,
        deck_name: str,
        note_type: str,
        fields: Dict[str, Any],
        tags: List[str] = [],
        allow_duplicates: bool = True,
    ) -> int:
        """Adds a note to a specified deck.

        Args:
            deck_name: Name of the deck to add to.
            note_type: Type of the note.
            fields: Fields and their values, in the format {"field1": val1, "field2": val2, ...}
            tags: A list of tags to add.
            allow_duplicates: Whether to allow for duplicate cards in the deck.

        Returns:
            ID of the created note.
        """
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
        self,
        deck_name: str,
        note_type: str,
        fields_list: List[Dict[str, Any]],
        tags: List[str] = [],
        allow_duplicates: bool = True,
    ) -> None:
        """Adds multiple notes to a deck.

        Assumes the notes are added to the same deck, are of the same type, and add the same tags.

        Args:
            deck_name: Name of the deck to add to.
            note_type: Type of the notes.
            fields_list: A list of fields and their values.
                Each element of the list in the format {"field1": val1, "field2": val2, ...}.
            tags: Tags to add.
            allow_duplicates: Whether to allow for duplicate cards in the deck.
        """
        print("Adding notes...")
        for fields in fields_list:
            self.add_note(deck_name, note_type, fields, tags)
        print(f"Added {len(fields_list)} words to {deck_name}.")

    def send_request(self, action: str, **params) -> Any:
        """Sends a request to the AnkiConnect API with the specified action and parameters.

        Args:
            action: The action to perform in the API.
            **params: An arbitrary number of parameters. Specifics depend on the action.

        Raises:
            RuntimeError: An error was returned in the response.

        Returns:
            The response of the API.
        """
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
    """Class representing the Vocabulary Builder from Kindle.

    The class establishes a connection with the database on initialization.
    """

    def __init__(self, path="/Volumes/Kindle/system/vocabulary/vocab.db"):
        self.connect_db(path)

    def connect_db(self, path: str):
        """Connects to the Kindle Vocabulary database.

        If the connection fails, it quits the program.

        Args:
            path: Path to the database.
        """
        try:
            self.conn = sqlite3.connect(path)
        except sqlite3.DatabaseError as e:
            print(
                "Couldn't connect to Vocabulary Builder. Make sure your Kindle is connected."
            )
            quit()

    def import_all_words(self) -> List[Dict[str, str]]:
        """Imports all unmastered words from the Vocabulary Builder.

        Returns:
            A list of imported words.
            Format of each element: {"word": actual word, "usage": the word's context}.
        """
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
