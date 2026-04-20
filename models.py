"""
models.py
---------
Core data structures for the music player.

Classes
-------
Song
    Represents a single track (title + artist).
Node
    A single link in a doubly linked list, wrapping one Song.
MusicPlayer
    A playlist implemented as a doubly linked list with full playback
    controls, volume, repeat, shuffle, and elapsed-time tracking.
"""

import time
import random


# ──────────────────────────────────────────────────────────────────────────────
# Song
# ──────────────────────────────────────────────────────────────────────────────

class Song:
    """
    Represents a single music track.

    Attributes
    ----------
    title : str
        The title of the song.
    artist : str
        The name of the artist or artists.
    """

    def __init__(self, title: str, artist: str) -> None:
        self.title  = title
        self.artist = artist

    def __str__(self) -> str:
        """Return a human-readable ``'Title - Artist'`` string."""
        return f"{self.title} - {self.artist}"


# ──────────────────────────────────────────────────────────────────────────────
# Node
# ──────────────────────────────────────────────────────────────────────────────

class Node:
    """
    A single link in a doubly linked list.

    Each node wraps one Song and holds pointers to both neighbours,
    enabling O(1) forward and backward navigation through a playlist.

    Attributes
    ----------
    song : Song
        The track stored in this node.
    next : Node or None
        Pointer to the next node (None if this is the tail).
    prev : Node or None
        Pointer to the previous node (None if this is the head).
    """

    def __init__(self, song: Song) -> None:
        self.song = song
        self.next: "Node | None" = None
        self.prev: "Node | None" = None


# ──────────────────────────────────────────────────────────────────────────────
# MusicPlayer
# ──────────────────────────────────────────────────────────────────────────────

class MusicPlayer:
    """
    A named playlist backed by a doubly linked list.

    Supports adding and removing songs, sequential and shuffled playback,
    repeat mode, volume control, and real-time elapsed-time tracking.

    Attributes
    ----------
    name : str
        Display name of this playlist.
    head : Node or None
        First node in the linked list.
    tail : Node or None
        Last node in the linked list.
    current : Node or None
        The node that is currently selected or playing.
    is_playing : bool
        True while a song is actively playing.
    volume : int
        Playback volume in the range 0–100. Default is 50.
    repeat : bool
        When True, the playlist loops back to the head after the last song.
    shuffle : bool
        When True, ``next_song`` picks a random track instead of the next one.
    play_start_time : float or None
        ``time.time()`` stamp recorded when the current song started.
        Reset to None whenever playback is paused.
    elapsed_before_pause : float
        Accumulated seconds played before the most recent pause, so that
        progress survives pause/resume cycles correctly.
    """

    def __init__(self, name: str = "Default") -> None:
        self.name                            = name
        self.head:     "Node | None"         = None
        self.tail:     "Node | None"         = None
        self.current:  "Node | None"         = None
        self.is_playing:        bool         = False
        self.volume:            int          = 50
        self.repeat:            bool         = False
        self.shuffle:           bool         = False
        self.play_start_time:   "float|None" = None
        self.elapsed_before_pause: float     = 0.0

    # ── Adding / removing ─────────────────────────────────────────────────────

    def add_song(self, song: Song) -> None:
        """
        Append a song to the end of the playlist.

        If the playlist is empty the new node also becomes ``current`` so
        playback can begin immediately without a separate selection step.

        Parameters
        ----------
        song : Song
            The track to append.
        """
        new_node = Node(song)

        if not self.head:
            # Empty playlist — all three pointers point to the only node
            self.head = self.tail = new_node
            self.current = self.head
        else:
            # Non-empty — attach after the tail and advance the tail pointer
            self.tail.next = new_node
            new_node.prev  = self.tail
            self.tail      = new_node

        print(f"Added: {song}")

    def delete_song(self, position: int) -> None:
        """
        Remove the song at a 1-based position from the playlist.

        Relinks surrounding nodes and updates ``head``, ``tail``, and
        ``current`` so the list stays consistent after deletion.

        Parameters
        ----------
        position : int
            1-based index of the song to remove.
        """
        if not self.head:
            print("Playlist is empty")
            return

        # Walk forward until the node at the target index is reached
        temp  = self.head
        index = 1
        while temp and index < position:
            temp  = temp.next
            index += 1

        if not temp:
            print("Invalid position")
            return

        # Relink the previous neighbour, or promote the next node to head
        if temp.prev:
            temp.prev.next = temp.next
        else:
            self.head = temp.next

        # Relink the next neighbour, or retract the tail to the previous node
        if temp.next:
            temp.next.prev = temp.prev
        else:
            self.tail = temp.prev

        # If the deleted node was current, move to the nearest surviving node
        if self.current == temp:
            self.current = temp.next or temp.prev

        print(f"Deleted: {temp.song}")

    def clear(self) -> None:
        """Remove every song and reset all node pointers to None."""
        self.head = self.tail = self.current = None
        print("Playlist cleared")

    # ── Playback ──────────────────────────────────────────────────────────────

    # Simulated song duration in seconds.
    # Every song is treated as 3 minutes long. When total elapsed time
    # exceeds this value the player auto-advances to the next song.
    SONG_DURATION: int = 180

    def check_and_advance(self) -> None:
        """
        Check whether the current song has exceeded its simulated duration
        and auto-advance to the next song if it has.

        Called at the start of each playback menu loop iteration so that
        auto-advance is triggered the next time the user interacts with the
        menu, without requiring a background thread.

        Auto-advance only fires when:
        - A song is actively playing (not paused).
        - Total elapsed time has reached or exceeded ``SONG_DURATION``.

        Notes
        -----
        When repeat is ON, ``next_song()`` wraps back to the head of the
        playlist, so auto-advance still works — the playlist just loops.
        When the last song in the playlist ends and repeat is OFF,
        ``next_song()`` prints "End of playlist" and stays put.
        """
        if not self.is_playing or not self.play_start_time:
            return   # paused or nothing playing — nothing to check

        # Total elapsed = banked time + live time since last play/resume
        total_elapsed = self.elapsed_before_pause + (time.time() - self.play_start_time)

        if total_elapsed >= self.SONG_DURATION:
            print(f"\n  ♪ '{self.current.song}' finished — auto-advancing...")
            self.next_song()   # respects shuffle and repeat settings

    def play(self) -> None:
        """
        Start playing the current song.

        Records ``play_start_time`` as the reference point for elapsed-time
        calculations, and resets ``elapsed_before_pause`` because this is a
        fresh play of a new song.
        """
        if not self.current:
            print("Playlist is empty")
            return

        self.is_playing           = True
        self.play_start_time      = time.time()  # anchor point for elapsed time
        self.elapsed_before_pause = 0.0          # new song — reset accumulated time
        print(f"Currently playing: {self.current.song}")

    def pause(self) -> None:
        """
        Pause playback and bank the elapsed time.

        Adds the seconds played since the last resume to
        ``elapsed_before_pause`` so ``show_progress`` stays accurate
        after the track is resumed.
        """
        if self.is_playing and self.play_start_time:
            # Bank seconds played since the last resume before clearing the timer
            self.elapsed_before_pause += time.time() - self.play_start_time
            self.play_start_time = None

        self.is_playing = False
        print("Paused")

    def resume(self) -> None:
        """
        Resume playback of the current song from where it was paused.

        Unlike ``play()``, which resets ``elapsed_before_pause`` to zero
        and treats the song as freshly started, ``resume()`` picks up the
        accumulated time exactly where ``pause()`` left off.

        Does nothing if the song is already playing or no song is selected.
        """
        if not self.current:
            print("No song selected.")
            return

        if self.is_playing:
            print(f"Already playing: {self.current.song}")
            return

        # Keep elapsed_before_pause intact — just restart the timer from now
        self.is_playing      = True
        self.play_start_time = time.time()
        print(f"Resumed: {self.current.song}")

    def next_song(self) -> None:
        """
        Advance to the next song according to the active mode.

        Logic
        -----
        1. Shuffle ON  → delegate to ``_play_random_song``.
        2. More songs remain → move one step forward in the list.
        3. End of list + Repeat ON → wrap back to the head.
        4. End of list + Repeat OFF → notify and stay put.
        """
        if self.shuffle:
            self._play_random_song()
        elif self.current and self.current.next:
            self.current = self.current.next
            self.play()
        elif self.repeat:
            self.current = self.head   # loop back to the beginning
            self.play()
        else:
            print("End of playlist")

    def previous_song(self) -> None:
        """
        Go back to the previous song.

        Does nothing and prints a notice if the current song is already
        the first track in the list.
        """
        if self.current and self.current.prev:
            self.current = self.current.prev
            self.play()
        else:
            print("No previous song")

    def _play_random_song(self) -> None:
        """
        Pick and play a random song, excluding the current one.

        Traverses the list to collect all nodes, removes the current node
        from the candidate pool, then calls ``random.choice``. If the
        playlist has only one song that song is simply replayed.

        Notes
        -----
        This is a private helper method. External code should call
        ``next_song`` (which routes here when shuffle is enabled).
        """
        all_nodes: list = []
        temp = self.head
        while temp:
            all_nodes.append(temp)
            temp = temp.next

        if len(all_nodes) <= 1:
            # Only one song in the list — nothing else to choose
            self.play()
            return

        # Exclude the currently playing node to prevent back-to-back repeats
        candidates = [n for n in all_nodes if n != self.current]
        self.current = random.choice(candidates)
        self.play()

    # ── Settings ──────────────────────────────────────────────────────────────

    def change_volume(self, vol: int) -> None:
        """
        Set the playback volume.

        Parameters
        ----------
        vol : int
            New volume level. Must be between 0 and 100 inclusive.
        """
        if 0 <= vol <= 100:
            self.volume = vol
            print(f"Volume set to {self.volume}")
        else:
            print("Invalid volume. Please enter a value between 0 and 100.")

    def toggle_repeat(self) -> None:
        """Flip repeat mode and print the updated state."""
        self.repeat = not self.repeat
        print("Repeat ON" if self.repeat else "Repeat OFF")

    def toggle_shuffle(self) -> None:
        """Flip shuffle mode and print the updated state."""
        self.shuffle = not self.shuffle
        print("Shuffle ON" if self.shuffle else "Shuffle OFF")

    # ── Display ───────────────────────────────────────────────────────────────

    def show_playlist(self) -> None:
        """
        Print every song in the playlist with its 1-based position number.

        The currently selected song is prefixed with ``->``.
        A short header shows the playlist name, shuffle state, and repeat state.
        """
        if not self.head:
            print("Playlist empty")
            return

        print(f"\nPlaylist : {self.name}")
        print(f"Shuffle  : {'ON' if self.shuffle else 'OFF'}  |  "
              f"Repeat : {'ON' if self.repeat else 'OFF'}")
        print()

        temp  = self.head
        index = 1
        while temp:
            marker = "->" if temp == self.current else "  "
            print(f"{marker} {index}. {temp.song}")
            temp  = temp.next
            index += 1

    def show_progress(self) -> None:
        """
        Display how long the current song has been playing.

        Combines ``elapsed_before_pause`` (time banked across previous
        play segments) with the live seconds since the last resume.
        When paused, only the banked time is shown.
        """
        if not self.current:
            print("No song selected.")
            return

        if self.is_playing and self.play_start_time:
            # Still playing: banked time + time since last resume
            total = self.elapsed_before_pause + (time.time() - self.play_start_time)
        else:
            # Paused: show only the banked total
            total = self.elapsed_before_pause

        minutes = int(total) // 60
        seconds = int(total) % 60

        print(f"  Song    : {self.current.song}")
        print(f"  Elapsed : {minutes}m {seconds:02d}s")
        print(f"  Status  : {'Playing' if self.is_playing else 'Paused'}")
