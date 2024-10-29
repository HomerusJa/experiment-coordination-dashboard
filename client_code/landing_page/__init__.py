from ._anvil_designer import landing_pageTemplate
from anvil import *
import anvil.server


class landing_page(landing_pageTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
