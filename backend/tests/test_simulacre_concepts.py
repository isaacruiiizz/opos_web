import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from routers.simulacre import extract_concepts

def test_extract_basic():
    result = extract_concepts("Configura el servidor DHCP per assignar adreces IP")
    assert "dhcp" in result
    assert "servidor" in result
    assert len(result) <= 3

def test_extract_ignores_stopwords():
    result = extract_concepts("El la els les de que un una")
    assert result == []

def test_extract_short_words_ignored():
    # paraules de menys de 4 lletres s'ignoren
    result = extract_concepts("com fer amb una xarxa")
    assert "xarxa" in result
    assert "fer" not in result

def test_extract_max_3():
    result = extract_concepts("servidor proxy tallafoc encriptació certificat autenticació")
    assert len(result) == 3

def test_extract_no_duplicates():
    result = extract_concepts("servidor servidor servidor proxy")
    assert result.count("servidor") == 1
