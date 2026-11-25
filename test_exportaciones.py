import unittest,zipfile
from backend.exportaciones import pdf,xlsx,modelo,TIPOS
from backend.reportes import periodo
import test_reportes
from test_pedidos import NIT
class ExportTest(unittest.TestCase):
    def setUp(self):
        self.fixture=test_reportes.ReportesTest();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
    def test_todos_formatos(self):
        for tipo,(_,fn) in TIPOS.items():
            with self.subTest(tipo=tipo):
                j=fn(self.fixture.c,NIT,self.fixture.p);self.assertTrue(pdf(tipo,j).read().startswith(b'%PDF-'))
                with zipfile.ZipFile(xlsx(tipo,j)) as z:self.assertIsNone(z.testzip());self.assertIn('xl/worksheets/sheet1.xml',z.namelist())
    def test_historico(self):
        j=TIPOS['productos'][1](self.fixture.c,NIT,periodo('2026-10-31','2026-10-31'));self.assertIsNone(modelo('productos',j)[4][0][4]);self.assertEqual(modelo('productos',j)[4][0][5],2)
    def test_formula_como_texto(self):
        j=TIPOS['productos'][1](self.fixture.c,NIT,self.fixture.p);j['productos'][0]['nombre']='=1+1'
        with zipfile.ZipFile(xlsx('productos',j)) as z:
            self.assertIn(b'=1+1',z.read('xl/sharedStrings.xml'));self.assertNotIn(b'<f>',z.read('xl/worksheets/sheet1.xml'))
    def test_sin_datos(self):
        for tipo,(_,fn) in TIPOS.items():
            j=fn(self.fixture.c,NIT,periodo('2025-01-01','2025-01-01'));self.assertTrue(pdf(tipo,j).read().startswith(b'%PDF-'));self.assertTrue(xlsx(tipo,j).read().startswith(b'PK'))
if __name__=='__main__':unittest.main()
