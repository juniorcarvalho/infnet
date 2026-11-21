from langchain_core.tools import BaseTool

from tools.conversao_tool import ConversaoTool
from tools.cotacao_tool import CotacaoTool
from tools.juros_compostos_tool import JurosCompostosTool
from tools.taxa_juros_tool import TaxaJurosTool


def get_tools() -> list[BaseTool]:
    return [CotacaoTool(), TaxaJurosTool(), JurosCompostosTool(), ConversaoTool()]
