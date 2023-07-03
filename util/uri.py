def insert_db_into_uri(uri, db):
    """
    Inserts the database name into the MongoDB URI.

    Note: Make sure to only pass URIs that do not already have a database name.

    Args:
        uri (str): MongoDB URI without a database name.
        db (str): Name of the database to be inserted into the URI.

    Returns:
        str: Modified MongoDB URI with the database name.

    """
    q_index = str(uri).find('?')
    if q_index == -1:
        return uri
    query=uri[q_index:]
    base=uri[:q_index]
    return base+db+query

