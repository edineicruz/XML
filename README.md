# XML Fiscal Manager Pro

Sistema profissional de gestão de documentos fiscais XML com licenciamento baseado em assinatura.

## 🚀 Características

- **Processamento de XMLs Fiscais**: Suporte completo para NFe, NFCe, CTe, NFSe, MDFe, CCe, EPEC
- **Interface Moderna**: Interface gráfica intuitiva e responsiva
- **Carregamento Sob Demanda**: Banco de dados carregado apenas quando solicitado pelo usuário
- **Exportação Avançada**: Exportação para Excel e CSV com formatação personalizável
- **Filtros Inteligentes**: Busca e filtros avançados por tipo de documento
- **Licenciamento**: Sistema de assinatura integrado com Google Sheets
- **Performance Otimizada**: Carregamento assíncrono e processamento em lotes

## 📋 Pré-requisitos

- Python 3.8 ou superior
- PySide6
- openpyxl (para exportação Excel)
- requests (para validação de licença)

## 🛠️ Instalação

1. **Clone o repositório**:
```bash
git clone https://github.com/edineicruz/XML.git
cd XML
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Configure o arquivo de autenticação**:
   - Crie um arquivo `auth.key` na raiz do projeto
   - Adicione sua chave de licença

4. **Execute a aplicação**:
```bash
python main.py
```

## 🎯 Como Usar

### Inicialização
- A aplicação abre em tela cheia automaticamente
- O banco de dados **não é carregado automaticamente** para melhor performance
- Clique no botão "🗄️ Carregar Banco" para carregar os dados quando necessário

### Importação de XMLs
1. Clique em "Importar XMLs" para selecionar arquivos individuais
2. Ou clique em "Importar Pasta" para processar uma pasta inteira (inclui busca recursiva e extração de ZIPs)

### Visualização e Filtros
- Use a barra lateral para selecionar tipos específicos de documentos (NFe, NFCe, etc.)
- Utilize os filtros de busca para encontrar documentos específicos
- A tabela mostra informações completas dos documentos fiscais

### Exportação
- **Exportação Rápida**: Use os botões na barra de ferramentas
- **Exportação Configurável**: Acesse o menu "Exportação" → "Configurar Exportação"
- **Formatos Suportados**: Excel (.xlsx) e CSV

## 📁 Estrutura do Projeto

```
XML/
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Dependências Python
├── config.json            # Configurações da aplicação
├── auth.key               # Chave de autenticação (não versionado)
├── core/                  # Módulos principais
│   ├── config_manager.py  # Gerenciador de configurações
│   ├── auth_manager.py    # Sistema de autenticação
│   ├── database_manager.py # Gerenciador de banco de dados
│   └── xml_processor.py   # Processador de XMLs
├── ui/                    # Interface do usuário
│   ├── main_window.py     # Janela principal
│   ├── export_dialog.py   # Diálogo de exportação
│   └── settings_dialog.py # Configurações
├── models/                # Modelos de dados
│   └── xml_models.py      # Modelos XML
├── utils/                 # Utilitários
│   └── logger.py          # Sistema de logs
├── assets/                # Recursos (ícones, etc.)
└── logs/                  # Arquivos de log (não versionado)
```

## 🔧 Configuração

### Configurações da Aplicação
O arquivo `config.json` contém as configurações principais:

```json
{
  "ui": {
    "startup": {
      "start_maximized": true,
      "center_on_screen": true
    },
    "window_size": {
      "width": 1400,
      "height": 900
    }
  },
  "database": {
    "path": "xml_fiscal_data.db"
  },
  "license": {
    "sheets_url": "https://docs.google.com/spreadsheets/..."
  }
}
```

### Sistema de Licenciamento
- A aplicação valida a licença através do Google Sheets
- Suporte a diferentes tipos de assinatura (basic, pro, enterprise)
- Validação automática na inicialização

## 🚀 Melhorias Implementadas

### Performance
- ✅ **Carregamento sob demanda**: Banco carregado apenas quando solicitado
- ✅ **Inicialização rápida**: Aplicação abre instantaneamente
- ✅ **Processamento assíncrono**: Interface responsiva durante operações pesadas
- ✅ **Otimização de memória**: Carregamento em lotes para grandes volumes

### Interface
- ✅ **Tela cheia automática**: Aplicação abre maximizada
- ✅ **Botão de carregamento manual**: Controle total do usuário
- ✅ **Feedback visual**: Progresso e status claros
- ✅ **Interface moderna**: Design profissional e intuitivo

### Organização
- ✅ **Arquivos limpos**: Removidos arquivos desnecessários
- ✅ **Estrutura otimizada**: Código organizado e documentado
- ✅ **Versionamento**: Preparado para Git/GitHub

## 📝 Logs

A aplicação gera logs detalhados na pasta `logs/`:
- `xml_fiscal_manager_YYYYMMDD.log`: Log principal
- `database_YYYYMMDD.log`: Operações de banco de dados
- `auth_YYYYMMDD.log`: Autenticação e licenciamento
- `ui_YYYYMMDD.log`: Interface do usuário

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença Comercial - Sistema de Assinatura.

## 👨‍💻 Desenvolvido por

**Auditoria Notebook Team**
- Versão: 2.0.0
- Licença: Comercial - Baseada em Assinatura

## 🆘 Suporte

Para suporte técnico ou dúvidas sobre licenciamento, entre em contato através do sistema de issues do GitHub.

---

**XML Fiscal Manager Pro** - Sistema profissional para gestão de documentos fiscais XML brasileiros. 