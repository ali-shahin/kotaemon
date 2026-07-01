from kotaemon.loaders.quality_gated_pdf_loader import undecodable_ratio

# A fragment of the garbled output produced when a PDF's fonts lack a valid
# ToUnicode CMap (Arabic PDF), full of GLYPH<...> placeholders.
GARBLED = (
    "aJLglallu 0@šlšš UN}MGLYPH<EOT> ≥ "
    "sLGLYPH<ESC>GLYPH<DC3>« Uatl W‡M‡‡GLYPH<US>GLYPH<DC3>« "
    "ÊuGLYPH<US>L)«Ë WMGLYPH<DC4>UGLYPH<ESC>GLYPH<DC3>«"
)

CLEAN = (
    "This is a normal, well-formed English paragraph extracted from a PDF whose "
    "fonts carry a proper ToUnicode mapping. There is nothing undecodable here."
)


def test_clean_text_has_low_ratio():
    assert undecodable_ratio(CLEAN) < 0.15


def test_garbled_text_has_high_ratio():
    assert undecodable_ratio(GARBLED) > 0.15


def test_empty_text_is_zero():
    assert undecodable_ratio("") == 0.0


def test_control_chars_counted():
    # 5 clean chars + 5 control chars -> ratio 0.5
    assert undecodable_ratio("abcde\x00\x01\x02\x03\x04") == 0.5
