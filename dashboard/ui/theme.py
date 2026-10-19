"""
Bee-Brain Ground Control Station - Unified Design System & Theme
Calibrated against Google Stitch design specification (DESIGN.md)
"""

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QApplication

# ==============================================================================
# COLOR TOKENS (Calibrated Industrial Lab Palette)
# ==============================================================================

class Palette:
    # Planar Surface Stepping
    BG_CANVAS = "#171916"       # Base chassis substrate (60% dominant)
    BG_SIDEBAR = "#20231F"      # Docking structural sidebar
    BG_PANEL = "#272B25"        # Sub-docking / bay containers
    BG_CARD = "#30352D"         # Elevated instrument cards & interactive modules
    BG_INSET = "#171916"        # Recessed viewports, plots & terminal logs

    # Structural Hairline Partitioning
    BORDER_HAIRLINE = "#41463B" # 1px division rules
    BORDER_SUBTLE = "#2E332B"   # Low-contrast internal dividers

    # Typography Tones
    TEXT_PRIMARY = "#F0EEE5"    # High legibility primary data & labels
    TEXT_SECONDARY = "#B4B7A9"  # Secondary descriptors & channel tags
    TEXT_MUTED = "#898F80"      # Timestamps, register keys & annotations

    # Functional Telemetry & Status Accents
    ACCENT_COPPER = "#E58B45"   # Primary control state, armed toggles, active nav
    ACCENT_AMBER = "#E6BD67"    # Measurement callouts, cautions, warnings
    ACCENT_SAGE = "#8CB7A1"     # Calibrated nominal state, valid link, healthy power
    ACCENT_CRIMSON = "#D95D50"  # System fault, E-STOP, critical threshold, watchdog

    # Interactive States
    HOVER_BG = "#383E34"
    ACTIVE_BORDER = "#E6BD67"


# QColor objects for direct use in custom QPainter widgets (AltitudePlot, DroneCanvas)
QCOLOR_BG_CANVAS = QColor(Palette.BG_CANVAS)
QCOLOR_BG_SIDEBAR = QColor(Palette.BG_SIDEBAR)
QCOLOR_BG_PANEL = QColor(Palette.BG_PANEL)
QCOLOR_BG_CARD = QColor(Palette.BG_CARD)
QCOLOR_BG_INSET = QColor(Palette.BG_INSET)
QCOLOR_BORDER = QColor(Palette.BORDER_HAIRLINE)

QCOLOR_TEXT_PRIMARY = QColor(Palette.TEXT_PRIMARY)
QCOLOR_TEXT_SECONDARY = QColor(Palette.TEXT_SECONDARY)
QCOLOR_TEXT_MUTED = QColor(Palette.TEXT_MUTED)

QCOLOR_COPPER = QColor(Palette.ACCENT_COPPER)
QCOLOR_AMBER = QColor(Palette.ACCENT_AMBER)
QCOLOR_SAGE = QColor(Palette.ACCENT_SAGE)
QCOLOR_CRIMSON = QColor(Palette.ACCENT_CRIMSON)


# ==============================================================================
# TYPOGRAPHY SPECIFICATION
# ==============================================================================

FONT_FAMILY_PRIMARY = "IBM Plex Sans, Segoe UI, -apple-system, Arial, sans-serif"
FONT_FAMILY_MONO = "JetBrains Mono, Consolas, Courier New, monospace"


def get_ui_font(size: int = 10, bold: bool = False) -> QFont:
    """Standard UI sans-serif font."""
    font = QFont()
    font.setFamilies(["IBM Plex Sans", "Segoe UI", "Arial"])
    font.setPointSize(size)
    if bold:
        font.setBold(True)
    return font


def get_mono_font(size: int = 10, bold: bool = False) -> QFont:
    """Monospace font strictly scoped for telemetry readouts and registers."""
    font = QFont()
    font.setFamilies(["JetBrains Mono", "Consolas", "Courier New"])
    font.setPointSize(size)
    if bold:
        font.setBold(True)
    return font


# ==============================================================================
# MASTER QSS (Qt Style Sheet)
# ==============================================================================

DARK_QSS = f"""
/* -------------------------------------------------------------------------- */
/* GLOBAL RESET & BASE CANVAS                                                 */
/* -------------------------------------------------------------------------- */

QWidget {{
    background-color: {Palette.BG_CANVAS};
    color: {Palette.TEXT_PRIMARY};
    font-family: {FONT_FAMILY_PRIMARY};
    font-size: 13px;
    selection-background-color: {Palette.ACCENT_COPPER};
    selection-color: {Palette.BG_CANVAS};
}}

QMainWindow {{
    background-color: {Palette.BG_CANVAS};
}}

/* -------------------------------------------------------------------------- */
/* DOCKING SIDEBAR & CHASSIS BRANDING                                         */
/* -------------------------------------------------------------------------- */

#sidebar {{
    background-color: {Palette.BG_SIDEBAR};
    border-right: 1px solid {Palette.BORDER_HAIRLINE};
}}

#logo {{
    color: {Palette.ACCENT_COPPER};
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 0.4px;
    padding-bottom: 2px;
}}

#sidebarSubtitle {{
    color: {Palette.TEXT_MUTED};
    font-size: 9px;
    letter-spacing: 0.3px;
    font-weight: 500;
    padding-left: 2px;
}}

#sidebarSectionLabel {{
    color: {Palette.TEXT_MUTED};
    font-family: {FONT_FAMILY_MONO};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.8px;
    padding-left: 4px;
}}

#sidebarFooter {{
    background-color: {Palette.BG_CANVAS};
    border: 1px solid {Palette.BORDER_SUBTLE};
    border-radius: 3px;
}}

#sidebarFooterValue {{
    color: {Palette.TEXT_SECONDARY};
    font-family: {FONT_FAMILY_MONO};
    font-size: 9px;
}}

/* Navigation Action Buttons */
#navButton {{
    background-color: transparent;
    color: {Palette.TEXT_SECONDARY};
    border: 1px solid transparent;
    border-left: 3px solid transparent;
    border-radius: 3px;
    text-align: left;
    padding-left: 10px;
    padding-right: 8px;
    font-size: 12px;
    font-weight: 500;
    min-height: 32px;
}}

#navButton:hover {{
    background-color: {Palette.HOVER_BG};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_HAIRLINE};
    border-left: 3px solid {Palette.ACCENT_AMBER};
}}

#navButton[active="true"] {{
    background-color: {Palette.BG_PANEL};
    color: {Palette.ACCENT_COPPER};
    border: 1px solid {Palette.BORDER_SUBTLE};
    border-left: 3px solid {Palette.ACCENT_COPPER};
    font-weight: bold;
}}

/* -------------------------------------------------------------------------- */
/* HEADER & STATUS BAR FRAMES                                                 */
/* -------------------------------------------------------------------------- */

#header {{
    background-color: {Palette.BG_SIDEBAR};
    border-bottom: 1px solid {Palette.BORDER_HAIRLINE};
}}

#pageTitle {{
    color: {Palette.TEXT_PRIMARY};
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 0.2px;
}}

#headerReadout {{
    background-color: {Palette.BG_CANVAS};
    color: {Palette.TEXT_SECONDARY};
    border: 1px solid {Palette.BORDER_SUBTLE};
    border-radius: 3px;
    padding: 5px 9px;
    font-family: {FONT_FAMILY_MONO};
    font-size: 10px;
    font-weight: 500;
}}

#headerReadout[state="nominal"] {{
    color: {Palette.ACCENT_SAGE};
    border-color: {Palette.BORDER_HAIRLINE};
}}

#statusBar {{
    background-color: {Palette.BG_SIDEBAR};
    border-top: 1px solid {Palette.BORDER_HAIRLINE};
    font-family: {FONT_FAMILY_MONO};
    font-size: 10px;
}}

/* -------------------------------------------------------------------------- */
/* INSTRUMENT PANELS & CARDS                                                  */
/* -------------------------------------------------------------------------- */

QFrame {{
    border-color: {Palette.BORDER_HAIRLINE};
}}

QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    border: 1px solid {Palette.BORDER_HAIRLINE};
    border-radius: 4px;
    background-color: {Palette.BG_PANEL};
}}

/* -------------------------------------------------------------------------- */
/* BUTTONS (Machined Industrial Enclosure Style)                              */
/* -------------------------------------------------------------------------- */

QPushButton {{
    background-color: {Palette.BG_CARD};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_HAIRLINE};
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    min-height: 28px;
}}

QPushButton:hover {{
    background-color: {Palette.HOVER_BG};
    border-color: {Palette.ACCENT_AMBER};
    color: {Palette.TEXT_PRIMARY};
}}

QPushButton:pressed {{
    background-color: {Palette.BG_CANVAS};
    border-color: {Palette.ACCENT_COPPER};
}}

QPushButton:disabled {{
    background-color: {Palette.BG_PANEL};
    color: {Palette.TEXT_MUTED};
    border-color: {Palette.BORDER_SUBTLE};
}}

/* Primary Action Buttons */
QPushButton[primary="true"] {{
    background-color: {Palette.ACCENT_COPPER};
    color: {Palette.BG_CANVAS};
    border: 1px solid {Palette.ACCENT_AMBER};
    font-weight: bold;
}}

QPushButton[primary="true"]:hover {{
    background-color: #EF9B59;
}}

/* E-STOP & Critical Cutoff Buttons */
QPushButton[danger="true"] {{
    background-color: {Palette.ACCENT_CRIMSON};
    color: #FFFFFF;
    border: 1px solid #FF8E82;
    font-weight: bold;
}}

QPushButton[danger="true"]:hover {{
    background-color: #E86F63;
}}

/* -------------------------------------------------------------------------- */
/* COMBOBOXES & DROPDOWNS                                                     */
/* -------------------------------------------------------------------------- */

QComboBox {{
    background-color: {Palette.BG_CARD};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_HAIRLINE};
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    min-height: 28px;
}}

QComboBox:hover {{
    border: 1px solid {Palette.ACCENT_COPPER};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid {Palette.BORDER_HAIRLINE};
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}}

QComboBox QAbstractItemView {{
    background-color: {Palette.BG_CARD};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_HAIRLINE};
    selection-background-color: {Palette.ACCENT_COPPER};
    selection-color: {Palette.BG_CANVAS};
    outline: none;
    padding: 2px;
}}

/* -------------------------------------------------------------------------- */
/* INPUT FIELDS & NUMERICAL SPINNERS                                          */
/* -------------------------------------------------------------------------- */

QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {Palette.BG_INSET};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_HAIRLINE};
    border-radius: 4px;
    padding: 4px 8px;
    font-family: {FONT_FAMILY_MONO};
    font-size: 12px;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {Palette.ACCENT_COPPER};
}}

/* -------------------------------------------------------------------------- */
/* PROGRESS BARS & GAUGES                                                     */
/* -------------------------------------------------------------------------- */

QProgressBar {{
    background-color: {Palette.BG_INSET};
    border: 1px solid {Palette.BORDER_HAIRLINE};
    border-radius: 4px;
    text-align: center;
    color: {Palette.TEXT_PRIMARY};
    font-family: {FONT_FAMILY_MONO};
    font-size: 11px;
    font-weight: bold;
    min-height: 20px;
}}

QProgressBar::chunk {{
    background-color: {Palette.ACCENT_COPPER};
    border-radius: 3px;
}}

/* -------------------------------------------------------------------------- */
/* SLIDERS (Precision Machined Potentiometer Track)                           */
/* -------------------------------------------------------------------------- */

QSlider::groove:horizontal {{
    height: 4px;
    background: {Palette.BG_SIDEBAR};
    border: 1px solid {Palette.BORDER_HAIRLINE};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {Palette.ACCENT_COPPER};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {Palette.ACCENT_COPPER};
    border: 1px solid {Palette.ACCENT_AMBER};
    width: 12px;
    height: 20px;
    margin: -8px 0;
    border-radius: 2px;
}}

QSlider::handle:horizontal:hover {{
    background: {Palette.ACCENT_AMBER};
}}

/* -------------------------------------------------------------------------- */
/* SCROLLBARS (Minimal Recessed Troughs)                                       */
/* -------------------------------------------------------------------------- */

QScrollBar:vertical {{
    background-color: {Palette.BG_CANVAS};
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {Palette.BORDER_HAIRLINE};
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {Palette.ACCENT_COPPER};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {Palette.BG_CANVAS};
    height: 8px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: {Palette.BORDER_HAIRLINE};
    min-width: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {Palette.ACCENT_COPPER};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* -------------------------------------------------------------------------- */
/* LOG TERMINAL / TEXT EDITS                                                  */
/* -------------------------------------------------------------------------- */

QTextEdit, QPlainTextEdit {{
    background-color: {Palette.BG_INSET};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER_HAIRLINE};
    border-radius: 4px;
    font-family: {FONT_FAMILY_MONO};
    font-size: 11px;
}}

/* Shared instrument header and persistent system strip */
#headerBreadcrumb {{
    color: {Palette.TEXT_MUTED};
    font-family: {FONT_FAMILY_MONO};
    font-size: 10px;
    letter-spacing: 0.5px;
    padding-right: 4px;
}}

#headerMode {{
    background-color: {Palette.ACCENT_COPPER};
    color: {Palette.BG_CANVAS};
    border: 1px solid {Palette.ACCENT_AMBER};
    border-radius: 3px;
    padding: 5px 8px;
    font-family: {FONT_FAMILY_MONO};
    font-size: 10px;
    font-weight: 700;
}}

#headerReadout[state="fault"] {{
    color: {Palette.ACCENT_CRIMSON};
    border-color: {Palette.ACCENT_CRIMSON};
}}

#statusPrimary, #statusMetric, #statusWarning {{
    font-family: {FONT_FAMILY_MONO};
    font-size: 10px;
    padding-left: 5px;
    padding-right: 5px;
}}

#statusMetric {{
    color: {Palette.TEXT_SECONDARY};
    border-left: 1px solid {Palette.BORDER_SUBTLE};
}}

#statusWarning {{
    color: {Palette.ACCENT_AMBER};
    border-left: 1px solid {Palette.BORDER_SUBTLE};
}}
"""


def apply_theme(app: QApplication) -> None:
    """Applies the master Stitch design theme stylesheet to the Qt Application."""
    app.setStyleSheet(DARK_QSS)
