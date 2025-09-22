import sqlite3
import json
from datetime import datetime
from typing import Any, Optional, Union, Dict, List, Tuple
from Core import name

class DB:
	def __init__(self, db_path: str = f"Assets/{name}.db"):
		"""
		Initialize the database connection.
		
		Args:
			db_path (str): Path to the SQLite database file
		"""
		self.db_path = db_path
		self.conn = None
		self.cursor = None
		self._initialize_database()
		
	def _initialize_database(self) -> None:
		"""Initialize the database tables if they don't exist."""
		try:
			self.connect()
			
			# Create main table
			self.cursor.execute("""
				CREATE TABLE IF NOT EXISTS data (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					key TEXT NOT NULL UNIQUE,
					value TEXT,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				)
			""")
			
			# Create subdata table for nested data
			self.cursor.execute("""
				CREATE TABLE IF NOT EXISTS subdata (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					parent_key TEXT NOT NULL,
					subkey TEXT NOT NULL,
					subvalue TEXT,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					FOREIGN KEY (parent_key) REFERENCES data (key) ON DELETE CASCADE,
					UNIQUE(parent_key, subkey)
				)
			""")
			
			# Enable foreign keys
			self.cursor.execute("PRAGMA foreign_keys = ON")
			
			self.conn.commit()
			
		except sqlite3.Error as e:
			print(f"Database initialization error: {e}")
		finally:
			self.close()
		
	def connect(self) -> None:
		"""Establish connection to the database."""
		self.conn = sqlite3.connect(self.db_path)
		self.cursor = self.conn.cursor()
		
	def close(self) -> None:
		"""Close the database connection."""
		if self.conn:
			self.conn.close()
			self.conn = None
			self.cursor = None
			
	def __enter__(self):
		"""Context manager entry."""
		self.connect()
		return self
		
	def __exit__(self, exc_type, exc_val, exc_tb):
		"""Context manager exit."""
		self.close()
			
	def check(self) -> bool:
		"""
		Check if project setup is complete.
		
		Returns:
			bool: True if project setup is marked as done
		"""
		try:
			self.connect()
			self.cursor.execute("SELECT value FROM data WHERE key = 'done'")
			result = self.cursor.fetchone()
			
			if result:
				done_value = self._deserialize_value(result[0])
				return bool(done_value)
			return False
			
		except sqlite3.Error as e:
			print(f"Check error: {e}")
			return False
		finally:
			self.close()
			
	def setup(self, done: bool = True) -> bool:
		"""
		Mark project setup as complete or incomplete.
		
		Args:
			done (bool): True to mark setup as complete, False to mark as incomplete
			
		Returns:
			bool: True if successful
		"""
		try:
			self.connect()
			serialized_done = self._serialize_value(done)
			
			self.cursor.execute(
				"INSERT OR REPLACE INTO data (key, value, updated_at) VALUES (?, ?, ?)",
				('done', serialized_done, datetime.now().isoformat())
			)
			
			self.conn.commit()
			return True
			
		except sqlite3.Error as e:
			print(f"Setup error: {e}")
			return False
		finally:
			self.close()
			
	def _serialize_value(self, value: Any) -> str:
		"""
		Serialize Python objects to JSON string for storage.
		
		Args:
			value: Any Python object to serialize
			
		Returns:
			str: JSON string representation
		"""
		return json.dumps(value)
		
	def _deserialize_value(self, value_str: str) -> Any:
		"""
		Deserialize JSON string back to Python object.
		
		Args:
			value_str: JSON string to deserialize
			
		Returns:
			Original Python object
		"""
		if value_str is None:
			return None
		return json.loads(value_str)
		
	def add(self, key: str, value: Any) -> bool:
		"""
		Add a new key-value pair to the database.
		
		Args:
			key (str): The key identifier
			value: The value to store (can be any JSON-serializable object)
			
		Returns:
			bool: True if successful
		"""
		try:
			self.connect()
			serialized_value = self._serialize_value(value)
			
			self.cursor.execute(
				"INSERT OR REPLACE INTO data (key, value, updated_at) VALUES (?, ?, ?)",
				(key, serialized_value, datetime.now().isoformat())
			)
			
			self.conn.commit()
			return True
			
		except sqlite3.Error as e:
			print(f"Add error: {e}")
			return False
		finally:
			self.close()
			
	def subadd(self, key: str, subkey: str, subvalue: Any) -> bool:
		"""
		Add a subkey-value pair to an existing key.
		
		Args:
			key (str): The parent key
			subkey (str): The subkey identifier
			subvalue: The value to store
			
		Returns:
			bool: True if successful
		"""
		try:
			self.connect()
			
			# First, ensure the parent key exists
			self.cursor.execute("SELECT 1 FROM data WHERE key = ?", (key,))
			if not self.cursor.fetchone():
				# Create parent key if it doesn't exist
				self.add(key, {})
				self.connect()  # Reconnect after add()
			
			serialized_subvalue = self._serialize_value(subvalue)
			
			self.cursor.execute(
				"""INSERT OR REPLACE INTO subdata 
				   (parent_key, subkey, subvalue, updated_at) 
				   VALUES (?, ?, ?, ?)""",
				(key, subkey, serialized_subvalue, datetime.now().isoformat())
			)
			
			self.conn.commit()
			return True
			
		except sqlite3.Error as e:
			print(f"Subadd error: {e}")
			return False
		finally:
			self.close()
			
	def get(self, key: str) -> Optional[Any]:
		"""
		Get value for a specific key.
		
		Args:
			key (str): The key to retrieve
			
		Returns:
			The stored value or None if not found
		"""
		try:
			self.connect()
			self.cursor.execute("SELECT value FROM data WHERE key = ?", (key,))
			result = self.cursor.fetchone()
			
			if result:
				return self._deserialize_value(result[0])
			return None
			
		except sqlite3.Error as e:
			print(f"Get error: {e}")
			return None
		finally:
			self.close()
			
	def subget(self, key: str, subkey: str) -> Optional[Any]:
		"""
		Get subvalue for a specific key and subkey.
		
		Args:
			key (str): The parent key
			subkey (str): The subkey to retrieve
			
		Returns:
			The stored subvalue or None if not found
		"""
		try:
			self.connect()
			self.cursor.execute(
				"SELECT subvalue FROM subdata WHERE parent_key = ? AND subkey = ?",
				(key, subkey)
			)
			result = self.cursor.fetchone()
			
			if result:
				return self._deserialize_value(result[0])
			return None
			
		except sqlite3.Error as e:
			print(f"Subget error: {e}")
			return None
		finally:
			self.close()
			
	def get_all_subdata(self, key: str) -> Optional[Dict[str, Any]]:
		"""
		Get all subdata for a specific key.
		
		Args:
			key (str): The parent key
			
		Returns:
			Dict of all subkey-value pairs or None if not found
		"""
		try:
			self.connect()
			self.cursor.execute(
				"SELECT subkey, subvalue FROM subdata WHERE parent_key = ?",
				(key,)
			)
			results = self.cursor.fetchall()
			
			if results:
				return {subkey: self._deserialize_value(subvalue) for subkey, subvalue in results}
			return {}
			
		except sqlite3.Error as e:
			print(f"Get all subdata error: {e}")
			return None
		finally:
			self.close()
			
	def update(self, update_data: Dict[str, Any]) -> bool:
		"""
		Update multiple key-value pairs.
		
		Args:
			update_data: Dictionary with keys and values to update
			Can be {key: value} or {key: {subkey: subvalue}}
			
		Returns:
			bool: True if successful
		"""
		try:
			self.connect()
			
			for key, value in update_data.items():
				if isinstance(value, dict):
					# Handle subdata updates
					for subkey, subvalue in value.items():
						# Ensure parent key exists
						self.cursor.execute("SELECT 1 FROM data WHERE key = ?", (key,))
						if not self.cursor.fetchone():
							self.add(key, {})
							self.connect()  # Reconnect
						
						serialized_subvalue = self._serialize_value(subvalue)
						self.cursor.execute(
							"""INSERT OR REPLACE INTO subdata 
							   (parent_key, subkey, subvalue, updated_at) 
							   VALUES (?, ?, ?, ?)""",
							(key, subkey, serialized_subvalue, datetime.now().isoformat())
						)
				else:
					# Handle regular data updates
					serialized_value = self._serialize_value(value)
					self.cursor.execute(
						"INSERT OR REPLACE INTO data (key, value, updated_at) VALUES (?, ?, ?)",
						(key, serialized_value, datetime.now().isoformat())
					)
			
			self.conn.commit()
			return True
			
		except sqlite3.Error as e:
			print(f"Update error: {e}")
			return False
		finally:
			self.close()
			
	def fetchall(self) -> Dict[str, Any]:
		"""
		Fetch all data from the database.
		
		Returns:
			Dictionary containing all keys with their values and subdata
		"""
		try:
			self.connect()
			
			# Get all main data
			self.cursor.execute("SELECT key, value FROM data")
			main_data = {key: self._deserialize_value(value) for key, value in self.cursor.fetchall()}
			
			# Get all subdata and organize by parent key
			self.cursor.execute("SELECT parent_key, subkey, subvalue FROM subdata")
			subdata_results = self.cursor.fetchall()
			
			for parent_key, subkey, subvalue in subdata_results:
				if parent_key in main_data:
					if isinstance(main_data[parent_key], dict):
						main_data[parent_key][subkey] = self._deserialize_value(subvalue)
					else:
						# Convert to dict if it wasn't one
						main_data[parent_key] = {**main_data[parent_key], subkey: self._deserialize_value(subvalue)}
				else:
					main_data[parent_key] = {subkey: self._deserialize_value(subvalue)}
			
			return main_data
			
		except sqlite3.Error as e:
			print(f"Fetchall error: {e}")
			return {}
		finally:
			self.close()
			
	def remove(self, key: str, subkey: Optional[str] = None) -> bool:
		"""
		Remove a key or subkey from the database.
		
		Args:
			key (str): The key to remove
			subkey (str, optional): The subkey to remove (if any)
			
		Returns:
			bool: True if successful
		"""
		try:
			self.connect()
			
			if subkey:
				# Remove specific subkey
				self.cursor.execute(
					"DELETE FROM subdata WHERE parent_key = ? AND subkey = ?",
					(key, subkey)
				)
			else:
				# Remove entire key (cascade will remove subdata)
				self.cursor.execute("DELETE FROM data WHERE key = ?", (key,))
			
			self.conn.commit()
			return True
			
		except sqlite3.Error as e:
			print(f"Remove error: {e}")
			return False
		finally:
			self.close()
			
	def exists(self, key: str, subkey: Optional[str] = None) -> bool:
		"""
		Check if a key or subkey exists.
		
		Args:
			key (str): The key to check
			subkey (str, optional): The subkey to check
			
		Returns:
			bool: True if exists
		"""
		try:
			self.connect()
			
			if subkey:
				self.cursor.execute(
					"SELECT 1 FROM subdata WHERE parent_key = ? AND subkey = ?",
					(key, subkey)
				)
			else:
				self.cursor.execute("SELECT 1 FROM data WHERE key = ?", (key,))
			
			return self.cursor.fetchone() is not None
			
		except sqlite3.Error:
			return False
		finally:
			self.close()
			
	def count(self) -> Tuple[int, int]:
		"""
		Count total keys and subkeys.
		
		Returns:
			Tuple of (main_keys_count, subkeys_count)
		"""
		try:
			self.connect()
			
			self.cursor.execute("SELECT COUNT(*) FROM data")
			main_count = self.cursor.fetchone()[0]
			
			self.cursor.execute("SELECT COUNT(*) FROM subdata")
			sub_count = self.cursor.fetchone()[0]
			
			return main_count, sub_count
			
		except sqlite3.Error:
			return 0, 0
		finally:
			self.close()