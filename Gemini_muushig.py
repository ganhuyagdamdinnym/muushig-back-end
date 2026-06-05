import random

SYMBOLS = ['♠', '♥', '♦', '♣']
RANKS = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {rank: index for index, rank in enumerate(RANKS)}

class Card:
    def __init__(self, symbol, rank):
        self.symbol = symbol
        self.rank = rank

    def __repr__(self):
        return f"{self.rank}{self.symbol}"

class MuushigGame:
    def __init__(self):
        self.players = {
            'Та': {'score': 15, 'pass_count': 0, 'in_game': True, 'hand': []},
            'Бот 1': {'score': 15, 'pass_count': 0, 'in_game': True, 'hand': []},
            'Бот 2': {'score': 15, 'pass_count': 0, 'in_game': True, 'hand': []},
            'Бот 3': {'score': 15, 'pass_count': 0, 'in_game': True, 'hand': []},
            'Бот 4': {'score': 15, 'pass_count': 0, 'in_game': True, 'hand': []}
        }
        self.player_names = list(self.players.keys())
        self.dealer_idx = 0  # first dealer is player
        self.deck = []
        self.upCard = None

    def reset_deck(self):    #  Huzruu holino
        self.deck = [Card(symbol, rank) for symbol in SYMBOLS for rank in RANKS]
        random.shuffle(self.deck)

    def card_taraah(self):   # hun burt 5 huzur taraana
        self.reset_deck()
        for player in self.players.values():
            player['hand'] = []
        
        # 5 cards for everyone
        for _ in range(5):
            for name in self.player_names:
                self.players[name]['hand'].append(self.deck.pop())
        
        # Gazriin mod(Delgesen card)
        self.upCard = self.deck.pop()

    def huzur_tavih_durem(self, hand, lead_card):
        """Card tavih durem"""
        if not lead_card:
            return hand  # Turuund garc baigaa bol durin huzur hayna

        lead_symbol = lead_card.symbol
        lead_rank = lead_card.rank

        # Gazriin modnii dursnuudiig haih
        upCard_cards = [c for c in hand if c.symbol == self.upCard.symbol]
        # Garsan dursnuudte ijil dursnuudig haij beldeh
        same_symbol = [c for c in hand if c.symbol == lead_symbol]

        if lead_rank == 'A':
            # 1. Gazriin modni tamga tavibal zaaval gazriin modnii huzur ugnu
            if lead_symbol == self.upCard.symbol:
                if upCard_cards:
                    return upCard_cards
                return hand  # Gazrin modni huzur baihgui tohioldold duriin huzur ugnu

            # 2. engiin tamgaar garval zaaval gazrin modoor idej davuulna
            else:
                if upCard_cards:
                    return upCard_cards  # zaaval gazrin modoor idne
                if same_symbol:
                    return same_symbol  # gazrin mod baihgui bol ijil dursnii huzur ugnu
                return hand  # alin c bhgu bol durin huzur tavina


    def evaluate_trick(self, trick_cards, lead_symbol):
        """Тойргийн ялагчийг тодруулах"""
        best_player = None
        best_card = None

        for player, card in trick_cards.items():
            if best_card is None:
                best_player = player
                best_card = card
                continue

            # Шинэ хөзөр хөг, хуучин хөзөр хөг биш бол шинэ нь илүү
            if card.symbol == self.upCard.symbol and best_card.symbol != self.upCard.symbol:
                best_player = player
                best_card = card
            # Хоёулаа ижил дүрс заавал (хоёулаа хөг эсвэл хоёулаа lead_symbol)
            elif card.symbol == best_card.symbol:
                if RANK_VALUES[card.rank] > RANK_VALUES[best_card.rank]:
                    best_player = player
                    best_card = card
        return best_player

    def play_round(self):
        dealer_name = self.player_names[self.dealer_idx]
        starter_idx = (self.dealer_idx + 1) % len(self.player_names)
        starter_name = self.player_names[starter_idx]

        self.card_taraah()

        print("\n" + "="*50)
        print(f"★ АЖИЛ ХИЙСЭН (Тараасан): {dealer_name} | ТОЙРОГ ЭХЛЭХ: {starter_name}")
        print(f"★ ГАЗРЫН МОД: {self.upCard}")
        print("="*50)

        # 1. Dealer gazriin modoo avah eseh
        if dealer_name == 'Та':
            print(f"Таны хөзрүүд: {self.players['Та']['hand']}")
            choice = input(f"Та газрын мод [{self.upCard}]-ийг авах уу? (y/n): ").lower()
            if choice == 'y':
                for idx, card in enumerate(self.players['Та']['hand']):
                    print(f"{idx}: {card}", end=" | ")
                print()
                discard_idx = int(input("Хаях хөзрийн дугаарыг сонгоно уу: "))
                self.players['Та']['hand'].pop(discard_idx)
                self.players['Та']['hand'].append(self.upCard)
                print(f"Та газрын мод авлаа! Шинэ хөзөр: {self.players['Та']['hand']}")
        else:
            # Bot cardaa saijruulval hamgiin muu cardaa hayah
            bot_hand = self.players[dealer_name]['hand']
            bot_hand.sort(key=lambda c: RANK_VALUES[c.rank])
            if bot_hand[0].symbol != self.upCard.symbol and RANK_VALUES[bot_hand[0].rank] < RANK_VALUES['J']:
                discarded = bot_hand.pop(0)
                bot_hand.append(self.upCard)
                print(f" {dealer_name} газрын модыг авч, {discarded}-ийг хаялаа.")

        # 2. In or Out 
        active_players = []
        # Nar zuw toirc asuuna
        decision_order = self.player_names[starter_idx:] + self.player_names[:starter_idx]

        for name in decision_order:
            # 3 daraallaj unjsun esehiig shalgana
            must_play = self.players[name]['pass_count'] >= 3

            if must_play:
                print(f"⚠️ {name} 3 дараалж өнжсөн тул энэ тойрогт ЗААВАЛ ОРНО!")
                self.players[name]['in_game'] = True
                active_players.append(name)
                continue

            if name == 'Та':
                print(f"\nТаны хөзөр: {self.players['Та']['hand']}")
                choice = input("Энэ үед тоглох уу? (y/n): ").lower()
                if choice == 'y':
                    self.players['Та']['in_game'] = True
                    self.players['Та']['pass_count'] = 0
                    active_players.append('Та')
                else:
                    self.players['Та']['in_game'] = False
                    self.players['Та']['pass_count'] += 1
                    print("Та өнжлөө.")
            else:
                # Bot choice (Ydaj 1 gazriin mod esvel А, К baival orno)
                bot_hand = self.players[name]['hand']
                has_upCard = any(c.symbol == self.upCard.symbol for c in bot_hand)
                has_big = any(RANK_VALUES[c.rank] >= RANK_VALUES['K'] for c in bot_hand)
                
                if has_upCard or has_big:
                    self.players[name]['in_game'] = True
                    self.players[name]['pass_count'] = 0
                    active_players.append(name)
                    print(f"{name} тоглохоор орлоо.")
                else:
                    self.players[name]['in_game'] = False
                    self.players[name]['pass_count'] += 1
                    print(f"{name} өнжлөө. (Дараалсан өнжилт: {self.players[name]['pass_count']})")

        # Herev zuwhun 1 hun uldvel ter n shuud round winner bolno
        if len(active_players) == 1:
            winner = active_players[0]
            print(f"\n🎉 Бүгд өнжсөн тул [{winner}] үеийг шууд авлаа! (-5 оноо)")
            self.players[winner]['score'] -= 5
            self.dealer_idx = (self.dealer_idx + 1) % len(self.player_names)
            return
        elif len(active_players) == 0:
            print("\nБүгд өнжсөн тул энэ үеийг хүчингүйд тооцов.")
            self.dealer_idx = (self.dealer_idx + 1) % len(self.player_names)
            return

        # 3. Mod solih
        print("\n--- ХӨЗӨР СОЛИХ ҮЕ ---")
        for name in active_players:
            if name == 'Та':
                print(f"Таны хөзөр: {self.players['Та']['hand']}")
                change_input = input("Солих хөзрүүдийн дугаарыг таслалаар тусгаарлаж оруулна уу (Жишээ нь: 0,2,3) эсвэл зүгээр Enter дар: ")
                if change_input.strip():
                    indices = sorted([int(i.strip()) for i in change_input.split(',')], reverse=True)
                    for idx in indices:
                        if 0 <= idx < len(self.players['Та']['hand']):
                            self.players['Та']['hand'].pop(idx)
                            self.players['Та']['hand'].append(self.deck.pop())
                    print(f"Таны шинэчилсэн хөзөр: {self.players['Та']['hand']}")
            else:
                # Bot gazriin mod bish sul huzruu hayna (Max 3 cards)
                bot_hand = self.players[name]['hand']
                to_change = [c for c in bot_hand if c.symbol != self.upCard.symbol and RANK_VALUES[c.rank] < RANK_VALUES['10']]
                change_count = min(len(to_change), 3)
                for _ in range(change_count):
                    # Bagaas n hasna
                    to_change.sort(key=lambda c: RANK_VALUES[c.rank])
                    bot_hand.remove(to_change[0])
                    bot_hand.append(self.deck.pop())
                    to_change.pop(0)
                if change_count > 0:
                    print(f"{name} {change_count} хөзөр солилоо.")

        # 4. Main game
        tricks_won = {name: 0 for name in active_players}
        current_lead = starter_name if starter_name in active_players else active_players[0]

        for trick_num in range(1, 6):
            print(f"\n--- хөзөр №{trick_num} ---")
            trick_cards = {}
            lead_symbol = None

            # Toglogcdiin hayah daraalal
            s_idx = active_players.index(current_lead)
            play_order = active_players[s_idx:] + active_players[:s_idx]

            for name in play_order:
                valid_cards = self.huzur_tavih_durem(self.players[name]['hand'], lead_symbol)

                if name == 'Та':
                    print(f"Таны хөзөр: {self.players['Та']['hand']}")
                    print("Таны хаях боломжтой хөзрүүд):")
                    for i, c in enumerate(self.players['Та']['hand']):
                        status = "✓" if c in valid_cards else "✗"
                        print(f"{i}: {c} [{status}]", end=" | ")
                    print()
                    
                    while True:
                        try:
                            choice = int(input("Хаях хөзрийн дугаарыг сонго: "))
                            chosen_card = self.players['Та']['hand'][choice]
                            if chosen_card in valid_cards:
                                self.players['Та']['hand'].pop(choice)
                                trick_cards['Та'] = chosen_card
                                break
                            print("❌ хөзөр барих дүрэм зөрчиж байна! [✓] тэмдэгтэйг сонгоно уу.")
                        except (ValueError, IndexError):
                            print("Буруу дугаар!")
                else:
                    # Бот зөв хөзрүүд дундаасаа хамгийн томыг нь хаяхыг хичээнэ
                    valid_cards.sort(key=lambda c: RANK_VALUES[c.rank], reverse=True)
                    chosen_card = valid_cards[0]
                    self.players[name]['hand'].remove(chosen_card)
                    trick_cards[name] = chosen_card
                    print(f"{name} хаясан: {chosen_card}")

                if lead_symbol is None:
                    lead_symbol = chosen_card.symbol

            # Round winner 
            winner = self.evaluate_trick(trick_cards, lead_symbol)
            print(f"Энэ хөзөрыг [{winner}] авлаа!")
            tricks_won[winner] += 1
            current_lead = winner

        # 5. Calculate points
        print("\n" + "-"*40)
        print("ҮЕ ТӨГСЛӨӨ! ОНООНЫ БАЙДАЛ:")
        for name in self.player_names:
            if name in active_players:
                won = tricks_won[name]
                if won == 0:
                    self.players[name]['score'] += 5
                    print(f"{name}: 0 хөзөр авч МУУШИГДЛАА! (+5 оноо). Нийт: {self.players[name]['score']}")
                else:
                    self.players[name]['score'] -= won
                    print(f"{name}: {won} хөзөр авлаа (-{won} оноо). Нийт: {self.players[name]['score']}")
            else:
                print(f"{name}: Өнжсөн. Нийт оноо: {self.players[name]['score']}")
        print("-"*40)

        # Next round dealer
        self.dealer_idx = (self.dealer_idx + 1) % len(self.player_names)

    def start_game(self):
        print(" МУУШИГ ТОГЛООМОНД ТАВТАЙ МОРИЛ!")
        print("Дүрэм: Бүгд 15 оноотой эхэлнэ. 0 оноонд хүрвэл хожно. 3 дараалж өнжвөл заавал орно.")
        
        while True:
            self.play_round()

            # Check points
            winners = [name for name, info in self.players.items() if info['score'] <= 0]
            if winners:
                print(f"\nТоглоом дууслаа! Ялагч: {', '.join(winners)}")
                break

            cont = input("\nДараагийн round-ыг эхлүүлэх үү? (y/n): ")
            if cont.lower() != 'y':
                print("Тоглоомыг дуусгалаа. Баяртай!")
                break

if __name__ == "__main__":
    game = MuushigGame()
    game.start_game()