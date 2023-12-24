
# capsWatcher
capsWatcher é um software criado em Python usando o framework PyQt para indicar o estado de teclas de alternância na tela utilizando overlays baseados em imagem, permitindo customização e criação de temas pela comunidade com facilidade. O projeto foi criado baseado na necessidade de algo *opensource* que seja elegante e personalizável, algo para que o usuário possa criar o próprio estilo de overlay. 

# O serviço capsWatcher
O serviço capsWatcher **`capsWatcher.py`** foi criado usando a API pywin32 para comunicar entre módulos e funções do Windows com o Python para obter o estado das teclas em tempo real, e claramente PyQt para exibir o overlay em tela que se sobrepõe sobre todas as janelas utilizando flags StayOnTop do Windows, deixando claro que exceto para executáveis que utilizam comunicação direta com a placa gráfica para renderizações, como jogos ou quaisquer aplicações utilizando DirectX ou OpenGL, elas sobrepõem e ignoram a flag StayOnTop do Windows.

O overlay é exibido em tela independente de qual tela seja pois o capsWatcher exibe o overlay baseado na tela onde está o cursor do mouse, então, caso tenha mais de um monitor, o overlay será exibido no monitor onde o cursor do mouse estiver presente, permitindo assim uma flexibilidade para usuários com 2 ou mais monitores.


<p align="center"><img src="https://i.imgur.com/oEFmote.gif"></p>

Comunicando com os dados do arquivo de configuração o capsWatcher é capaz de monitorar mais de uma tecla de alternância sem criar diversos processos filhos a partir do primário e claramente utilizando pouquíssima CPU e RAM após carregar as variáveis e informações, basicamente o peso de uma pena para seus recursos.

Mantendo um ícone na área de notificações do Windows (na qual o usuário decide se ele é oculto ou não) é possível chamar a interface de configuração e configurar o overlay, encerrar ou recarregar as configurações do arquivo.

# A interface de configuração capsWatcher
A interface de configuração do capsWatcher **`capsWatcherInterface.py`** foi desenvolvida em conjunto com o serviço capsWatcher, que permite a configuração do overlay nas quais são; 
- Tempo de exibição do overlay na tela em ms(milisegundos)
- Tempo do efeito de fade-in/out em ms(milisegundos)
- Opacidade do overlay na tela
- Posição do overlay na tela
- Seleção de temas
- Seleção do esquema de cores (baseado no tema atual)
- Área de pré-visualização de como o overlay ficará na tela com as configurações atuais.
- Seleção de teclas que deseja monitorar
- Controle para iniciar ou parar o serviço capsWatcher.

 e também outras configurações da interface relacionado ao serviço como;

- Iniciar com o Windows
- Mostrar ou ocultar o ícone na área de tarefas
- Seleção de linguagem da interface de configurações
- Área para instalar novos temas (que podem ser feitos por você)
- Área para checar atualizações que também incluem seleção para nunca checar por atualizações
- Função para redefinir todas as configurações do capsWatcher para as padrões.

<br />
<p align="center">
    <img width="487" src="https://i.imgur.com/xnYpqBo.png">
    <img width="487" src="https://i.imgur.com/OUPH7Ss.png">
</p>

# Temas
A parte de temas do capsWatcher nasceu com a ideia de que sejam criados pela comunidade e caso queiram, serão integrados a esse repositório por meio de pull requests na pasta `contributed-themes` contanto que sigam as recomendações de como criar um tema abaixo e podendo até aparecer em uma próxima release do capsWatcher.

## Do que é constituído o tema ?
O tema é constituído em formato de arquivo ZIP com sua estrutura de diretórios (na qual iremos abordar logo abaixo), arquivos de imagem de overlay e o JSON com o nome do tema contendo informações sobre o tema para que de forma padronizada a interface de configuração do capsWatcher a consiga importar de maneira fácil e rápida. Ok, isso é interessante, mas como consigo criar o meu ?

## O arquivo de imagem
Os temas do capsWatcher podem ser feitos utlizando imagem em formato PNG Alpha, que suporte transparências, na qual recomendam-se ser nas dimensões de 128 pixels de altura e 128 pixels de largura, exatamente na proporção 1:1, (caso exceda, o preview na interface de configuração irá mostrar apenas os 128 pixels iniciais tanto x como y, o que será algo a corrigir em uma versão futura), porém podendo exceder tal tamanho pois o overlay o posiciona na tela calculando a dimensões da imagem, dimensão da tela e definindo a posição conforme selecionada pelo usuário. 

*OBS: Atualmente o capsWatcher suporta apenas o monitoramento de teclas de alternância como Num Lock, Caps Lock e Scroll Lock.*

## Regra de nomenclatura do arquivo de imagem
Além de ter a imagem preparada, precisamos renomeá-la para que o capsWatcher a encontre e a defina como a tecla associada, para isso utlizamos o [código da tecla](https://learn.microsoft.com/pt-br/dotnet/api/system.windows.forms.keys?view=windowsdesktop-8.0) e o estado em booleano como analogia descrita abaixo;

**`código da tecla + estado da tecla.png`**

Utilizando a analogia descrita acima, digamos que iremos fazer uma imagem customizada para a tecla Caps Lock no estado de desativada, então;

Código da tecla Caps Lock é **20** e o estado da tecla desativada em formato booleano é **0**

A soma textual dos itens resulta em um arquivo com o seguinte nome, **`200.png`**, esse é o nosso arquivo referente ao estado desativado da tecla Caps Lock.

## Estrutura do diretório de um tema

Para que tudo ocorra bem com os temas do capsWatcher, precisamos seguir algumas regras de estrutura de diretórios. 

Dentro da pasta `themes` do capsWatcher, é o local onde os temas são armazenados, cada um em sua pasta contendo o nome do tema na pasta em questão, dentro de cada subpasta do tema, há de ter o arquivo `*.json` do tema em questão, e as subpastas referentes aos esquemas de cores, entre eles `dark` ou `light` que podem ser definidos com outros nomes e atualizados no arquivo `*.json` que vamos abordar futuramente. 

Dentro de cada pasta de esquema de cores, deverão estar localizadas as imagens referentes as teclas que haverão suporte no tema atual seguindo a regra de nomenclatura citada anteriormente.

Abaixo segue o exemplo de estrutura de diretório a partir da pasta `themes` do próprio capsWatcher referente ao tema padrão "Elegant";

```bash
├── themes
│   ├── elegant # Pasta do tema
│   │   ├── dark # Pasta onde estão localizados as imagens referente ao modo escuro do tema
│   │   │   ├── 200.png # Imagem referente a tecla Caps Lock em seu estado desativado no modo escuro
│   │   │   ├── 201.png # Imagem referente a tecla Caps Lock em seu estado ativado no modo escuro
│   │   │   ├── 1440.png # Imagem referente a tecla Num Lock em seu estado desativado no modo escuro
│   │   │   ├── 1441.png # Imagem referente a tecla Num Lock em seu estado ativado no modo escuro
│   │   │   ├── 1450.png # Imagem referente a tecla Scroll Lock em seu estado desativado no modo escuro
│   │   │   ├── 1451.png # Imagem referente a tecla Scroll Lock em seu estado ativado no modo escuro
│   │   ├── light # Pasta onde estão localizados as imagens referente ao modo claro do tema
│   │   │   ├── 200.png # Imagem referente a tecla Caps Lock em seu estado desativado no modo claro
│   │   │   ├── 201.png # Imagem referente a tecla Caps Lock em seu estado ativado no modo claro
│   │   │   ├── 1440.png # Imagem referente a tecla Num Lock em seu estado desativado no modo claro
│   │   │   ├── 1441.png # Imagem referente a tecla Num Lock em seu estado ativado no modo claro
│   │   │   ├── 1450.png # Imagem referente a tecla Scroll Lock em seu estado desativado no modo claro
│   │   │   ├── 1451.png # Imagem referente a tecla Scroll Lock em seu estado ativado no modo claro
│   └── elegant.json # Arquivo JSON para identificação e suporte do tema ao capsWatcher
└────────────────────────
```

Desse modo, temos pronta a estrutura de diretórios de um tema para o capsWatcher.

## Modo claro e modo escuro aplicado aos temas

Porém como posso decidir que meu tema tenha uma aparência diferente caso o esquema de cores do Windows esteja no modo claro ou escuro ?

Basicamente para constituir os modos de cores do tema, além de ter sua imagem em formato PNG com as dimensões recomendadas, precisamos decidir se esse tema suportará para monitorar o Num Lock apenas em modo claro, ou Caps Lock apenas no modo escuro ou até mesmo Scroll Lock em ambos modos de cores.

Sabendo disso, para cada esquema de cor claro ou escuro, precisamos na pasta do tema (como estrutura de diretórios explicados acima) criar uma subpasta para cada esquema de cor (recomenda-se criar com os nomes padrão "dark" para modo escuro, e "light" para o modo claro), cada subpasta contendo suas imagens de overlay para atuar em ambos esquemas de cores, caso deseje, e lembre-se do nome dessas subpastas, iremos utilizá-la para criar o nosso arquivo JSON do tema.

Ok, montada as pastas de esquemas de cores e sua devida estrutura de diretórios, precisamos montar o arquivo JSON para que o capsWatcher reconheça o tema, sem ele, o capsWatcher não irá carregar o tema, então vamos para a parte do JSON.

## O arquivo JSON do tema
Cada tema obrigatoriamente tem seu arquivo JSON que deve ficar localizado na pasta raíz do tema (como explicado anteriormente na estrutura de diretórios de um tema), que contém informações para que o capsWatcher o identifique se suporta multiplos esquemas de cores, se o tema suporta o monitoramento de uma tecla específica dependendo do esquema de cor, além de informações gerais como, nome do tema e detalhes do criador.

O arquivo JSON de um tema é simples e com poucas chaves e valores, e lembre-se, é necessário que ele esteja na raíz da pasta do tema, abaixo segue o exemplo de um json do tema padrão "Elegant" do capsWatcher.

```json
{
    "theme": "elegant",
    "name": "Elegant",
    "creator": "Natã Andreghetone",
    "description": "The first and default capsWatcher theme's",
    "github_user": "nxtsoul",
    "creation_date": "2023-11-18 02:39:45",
    "darkMode": {
        "isSupported": true,
        "numLockSupport": true,
        "capsLockSupport": true,
        "scrollLockSupport": true,
        "overlayPath": "dark"
    },
    "lightMode": {
        "isSupported": true,
        "numLockSupport": true,
        "capsLockSupport": true,
        "scrollLockSupport": true,
        "overlayPath": "light"
    }
}
```

Visualizando o JSON do tema "Elegant", podemos perceber que o suporte das teclas se divide entre esquema de cores, sendo eles, `darkMode` e `lightMode`, e em cada um deles o suporte para cada tecla de alternância.

É importante também ressaltar que caso a chave `isSupported` da chave pai `darkMode` seja alterada para `false`, o capsWatcher entenderá que aquele tema não suporta o monitoramento no modo escuro de cor, independentemente se as chaves de suporte das teclas como `numLockSupport` estejam com o valor `true`. Então caso seu tema tenha suporte apenas para a tecla Num Lock, deixe a chave `isSupported` da chave pai `darkMode` com o valor `true`, e o valor da chave `numLockSupport` com o valor `true`, e assim por diante caso deseja suporte em outras teclas.

Finalizado essa etapa, já é possível zipar o tema e compartilhar via pull request para que esteja em próximas releases do capsWatcher.