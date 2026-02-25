from ..formats.hsbc_format import FormatoHSBC
# from ..formats.banorte_format import FormatoBanorte
# from ..formats.bbva_format import FormatoBBVA

class FormatFactory:
    """Fábrica para crear instancias de formatos bancarios"""
    
    _formatos = {
        'hsbc': FormatoHSBC,
        # 'banorte': FormatoBanorte,
        # 'bbva': FormatoBBVA,
    }
    
    @classmethod
    def crear_formato(cls, banco, mapeo, inputs_adicionales, filas_eliminar):
        """
        Crea una instancia del formato correspondiente al banco
        """
        formato_class = cls._formatos.get(banco)
        if not formato_class:
            raise ValueError(f"Formato no soportado para el banco: {banco}")
        
        return formato_class(mapeo, inputs_adicionales, filas_eliminar)