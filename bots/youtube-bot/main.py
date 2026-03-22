from gateway.router    import Router
from gateway.telegram  import TelegramGateway
from tools.youtube.tool import YouTubeTool

router = Router()
router.register(YouTubeTool())

# Future tools — uncomment when ready:
# from tools.pdf.tool  import PDFTool;  router.register(PDFTool())
# from tools.news.tool import NewsTool; router.register(NewsTool())

gateway = TelegramGateway(router)
app     = gateway.app