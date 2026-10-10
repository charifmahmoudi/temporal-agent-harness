"""Recognize the declared decoding signature across the Core exception bridge."""


def decoding_mechanism(chain):
    for error in chain:
        message = error["message"]
        expected = "Expected value to be str" in message and "bool" in message
        if error["type"] == "TypeError" and expected:
            return True
        # Core serializes nested failures into the outer RuntimeError instead
        # of retaining the original Python __cause__ chain on Replayer errors.
        if (error["type"] == "RuntimeError" and expected
                and "Failed decoding arguments" in message
                and "cause: Some(Failure" in message
                and 'r#type: "TypeError"' in message):
            return True
    return False
