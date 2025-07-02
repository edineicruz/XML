# Sistema de Atualizações Automáticas

## 🔄 Como Funciona

O XML Fiscal Manager Pro agora possui um sistema completo de verificação automática de atualizações que conecta diretamente ao GitHub para verificar novas versões.

### Características Principais

- ✅ **Verificação Automática**: Verifica atualizações a cada 24 horas por padrão
- ✅ **Verificação Manual**: Botão "Verificar Atualizações" na barra de ferramentas
- ✅ **Download Direto**: Baixa atualizações diretamente do GitHub
- ✅ **Interface Moderna**: Diálogo elegante com informações detalhadas
- ✅ **Notas de Versão**: Exibe automaticamente as novidades de cada versão
- ✅ **Comparação de Versões**: Sistema inteligente de comparação semântica

## 📋 Para o Desenvolvedor

### Como Criar uma Nova Versão

1. **Atualizar a Versão no Código**:
   ```python
   # Em core/config_manager.py
   "version": "2.1.0"  # Atualize aqui
   ```

2. **Fazer Commit e Push**:
   ```bash
   git add .
   git commit -m "v2.1.0: Novas funcionalidades e melhorias"
   git push origin main
   ```

3. **Criar um Release no GitHub**:
   - Vá para https://github.com/edineicruz/XML/releases
   - Clique em "Create a new release"
   - Configure:
     - **Tag version**: `v2.1.0`
     - **Release title**: `XML Fiscal Manager Pro v2.1.0`
     - **Description**: Descreva as novidades (suporta Markdown)
     - **Assets**: Anexe arquivos se necessário

4. **Publicar o Release**:
   - Clique em "Publish release"
   - O sistema automaticamente detectará a nova versão

### Formato das Notas de Versão

Use Markdown para formatar as notas de versão:

```markdown
## 🚀 Novidades

- **Nova funcionalidade**: Descrição da funcionalidade
- **Melhorias**: Lista de melhorias realizadas

## 🐛 Correções

- Corrigido problema X
- Resolvido bug Y

## ⚡ Performance

- Otimização no carregamento de dados
- Melhoria na interface do usuário
```

## 👥 Para o Usuário

### Verificação Automática

- A aplicação verifica automaticamente por atualizações a cada 24 horas
- Uma notificação discreta aparece quando há uma nova versão
- Não interfere no funcionamento normal da aplicação

### Verificação Manual

1. Clique no botão **"Verificar Atualizações"** na barra de ferramentas
2. O sistema conectará ao GitHub para buscar a versão mais recente
3. Se houver atualização, um diálogo aparecerá com as informações

### Diálogo de Atualização

O diálogo moderno mostra:

- **Versão Atual vs Nova Versão**: Comparação visual
- **Nome do Release**: Título da versão
- **Data de Publicação**: Quando foi lançada
- **Notas de Versão**: Novidades e melhorias
- **Opções**:
  - **Baixar Agora**: Download direto
  - **Ver no GitHub**: Abre a página do release
  - **Lembrar Depois**: Fecha o diálogo

### Download e Instalação

1. **Download Automático**: O arquivo é baixado em uma pasta temporária
2. **Notificação**: Sistema avisa quando o download está completo
3. **Localização**: Opção de abrir a pasta onde foi salvo
4. **Instalação Manual**: O usuário deve substituir os arquivos manualmente

## ⚙️ Configurações

### Configurações Disponíveis

- **Auto Check**: Ativar/desativar verificação automática
- **Check Interval**: Intervalo entre verificações (padrão: 24 horas)
- **GitHub Repo**: Repositório do GitHub (padrão: edineicruz/XML)
- **Notify Beta**: Notificar sobre versões beta/pré-lançamento

### Localização das Configurações

As configurações são armazenadas em `config.json`:

```json
{
  "update_settings": {
    "auto_check": true,
    "check_interval_hours": 24,
    "github_repo": "edineicruz/XML",
    "notify_beta": false,
    "auto_download": false,
    "last_check": "2024-01-15T10:30:00",
    "dismissed_versions": []
  }
}
```

## 🔧 Resolução de Problemas

### Erro de Conexão

**Problema**: "Erro de conexão: Unable to connect to GitHub"
**Solução**: 
- Verificar conexão com a internet
- Verificar se o GitHub está acessível
- Tentar novamente mais tarde

### Erro de Parsing

**Problema**: "Erro ao processar resposta"
**Solução**:
- Verificar se o repositório existe
- Verificar se há releases publicados
- Confirmar formato correto das versões

### Download Falha

**Problema**: Download não completa ou falha
**Solução**:
- Verificar espaço disponível em disco
- Verificar permissões da pasta temporária
- Tentar baixar manualmente do GitHub

## 📊 Logs

O sistema gera logs detalhados:

```
[INFO] Checking for updates from: https://api.github.com/repos/edineicruz/XML/releases/latest
[INFO] Update available: 2.1.0
[INFO] Performing automatic update check on startup
[INFO] Automatic update check skipped (not due yet or disabled)
```

## 🔒 Segurança

- **HTTPS Only**: Todas as conexões usam HTTPS
- **Verificação de Assinatura**: Verifica origem dos arquivos
- **Pasta Temporária**: Downloads em local seguro
- **Sem Execução Automática**: Nunca executa arquivos automaticamente

## 🎯 Próximas Melhorias

- [ ] **Auto-instalação**: Aplicar atualizações automaticamente
- [ ] **Rollback**: Voltar para versão anterior se necessário
- [ ] **Delta Updates**: Baixar apenas as diferenças
- [ ] **Notificação de Sistema**: Usar notificações do Windows
- [ ] **Agenda Customizada**: Mais opções de agendamento

---

**Nota**: Este sistema garante que os usuários sempre tenham acesso às versões mais recentes com todas as melhorias e correções de segurança. 