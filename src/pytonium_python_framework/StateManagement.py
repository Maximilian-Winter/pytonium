import json

class StateManager:
    def __init__(self):
        self.namespaces = {}  # Dictionary containing all namespaces

    def _ensure_namespace_exists(self, namespace):
        """Automatically create a namespace if it doesn't exist."""
        if namespace not in self.namespaces:
            self.namespaces[namespace] = {}  # Create a new dictionary for the namespace

    def set_state(self, namespace, key, value):
        self._ensure_namespace_exists(namespace)
        self.namespaces[namespace][key] = value  # Set the state

    def get_state(self, namespace, key):
        self._ensure_namespace_exists(namespace)
        return self.namespaces[namespace].get(key, None)  # Get the state value, return None if not found

    def remove_state(self, namespace, key):
        self._ensure_namespace_exists(namespace)
        if key in self.namespaces[namespace]:
            del self.namespaces[namespace][key]  # Remove the state

    def serialize_to_json(self):
        """Serialize the entire state to a JSON string."""
        return json.dumps(self.namespaces)

    def deserialize_from_json(self, json_str):
        """Deserialize a JSON string to populate the state."""
        try:
            self.namespaces = json.loads(json_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string provided for deserialization.")