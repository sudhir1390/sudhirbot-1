from gateway.router     import Router
from gateway.telegram   import TelegramGateway
from tools.youtube.tool import YouTubeTool
from tools.pdf.tool     import PDFTool
from tools.chart.tool   import ChartTool

router = Router()
router.register(YouTubeTool())
router.register(PDFTool())
router.register(ChartTool())

# Future tools — uncomment when ready:
# from tools.news.tool import NewsTool; router.register(NewsTool())

gateway = TelegramGateway(router)
app     = gateway.app